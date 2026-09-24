#include "ugv_nav2/traversability_layer.hpp"

#include <cmath>
#include <algorithm>

#include "pluginlib/class_list_macros.hpp"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "nav2_costmap_2d/cost_values.hpp"

PLUGINLIB_EXPORT_CLASS(ugv_nav2::TraversabilityLayer, nav2_costmap_2d::Layer)

namespace ugv_nav2
{

TraversabilityLayer::TraversabilityLayer()
: topic_name_("/perception/traversability_grid"),
  traversability_weight_(1.0),
  rolling_(false),
  new_data_(false),
  latest_grid_(nullptr)
{
}

TraversabilityLayer::~TraversabilityLayer()
{
}

void TraversabilityLayer::onInitialize()
{
  auto node = node_.lock();
  if (!node) {
    throw std::runtime_error{"Failed to lock node in TraversabilityLayer"};
  }

  declareParameter("enabled", rclcpp::ParameterValue(true));
  declareParameter("topic", rclcpp::ParameterValue(std::string("/perception/traversability_grid")));
  declareParameter("traversability_weight", rclcpp::ParameterValue(1.0));
  // rolling=true  → clear costmap window each frame (local costmap: responsive, no freeze)
  // rolling=false → accumulate obstacle history  (global costmap: planner remembers all seen obstacles)
  declareParameter("rolling", rclcpp::ParameterValue(false));

  node->get_parameter(name_ + ".enabled", enabled_);
  node->get_parameter(name_ + ".topic", topic_name_);
  node->get_parameter(name_ + ".traversability_weight", traversability_weight_);
  node->get_parameter(name_ + ".rolling", rolling_);

  RCLCPP_INFO(
    logger_, "TraversabilityLayer: rolling=%s (weight: %.2f)",
    rolling_ ? "true (local/responsive)" : "false (global/accumulate)",
    traversability_weight_);

  default_value_ = nav2_costmap_2d::FREE_SPACE;
  matchSize();
  current_ = true;

  rclcpp::SubscriptionOptions sub_opts;
  sub_opts.callback_group = callback_group_;
  grid_sub_ = node->create_subscription<nav_msgs::msg::OccupancyGrid>(
    topic_name_, rclcpp::SystemDefaultsQoS(),
    std::bind(&TraversabilityLayer::incomingGridCallback, this, std::placeholders::_1),
    sub_opts);

  RCLCPP_INFO(
    logger_, "TraversabilityLayer initialized. Subscribing to: %s (weight: %.2f)",
    topic_name_.c_str(), traversability_weight_);
}

void TraversabilityLayer::incomingGridCallback(const nav_msgs::msg::OccupancyGrid::SharedPtr msg)
{
  std::lock_guard<std::mutex> lock(data_mutex_);
  latest_grid_ = msg;
  new_data_ = true;
}

void TraversabilityLayer::updateBounds(
  double robot_x, double robot_y, double /*robot_yaw*/,
  double * min_x, double * min_y, double * max_x, double * max_y)
{
  if (!enabled_) {
    return;
  }

  // Omnidirectional expansion covering the maximum perception reach (8.0m) regardless of heading
  touch(robot_x + 8.0, robot_y + 8.0, min_x, min_y, max_x, max_y);
  touch(robot_x - 8.0, robot_y - 8.0, min_x, min_y, max_x, max_y);
}

void TraversabilityLayer::updateCosts(
  nav2_costmap_2d::Costmap2D & master_grid,
  int min_i, int min_j, int max_i, int max_j)
{
  if (!enabled_) {
    return;
  }

  nav_msgs::msg::OccupancyGrid::SharedPtr grid;
  {
    std::lock_guard<std::mutex> lock(data_mutex_);
    if (!latest_grid_) {
      return;
    }
    grid = latest_grid_;
  }

  std::string global_frame = layered_costmap_->getGlobalFrameID();
  std::string sensor_frame = grid->header.frame_id;

  geometry_msgs::msg::TransformStamped tf_stamp;
  try {
    tf_stamp = tf_->lookupTransform(
      global_frame, sensor_frame,
      tf2::TimePointZero,
      tf2::durationFromSec(0.08));
  } catch (const tf2::TransformException & ex) {
    RCLCPP_WARN_THROTTLE(
      logger_, *clock_, 2000,
      "TraversabilityLayer: TF lookup %s -> %s failed: %s",
      global_frame.c_str(), sensor_frame.c_str(), ex.what());
    return;
  }

  // Extract translation and 2D rotation from transform
  double tx = tf_stamp.transform.translation.x;
  double ty = tf_stamp.transform.translation.y;
  double qx = tf_stamp.transform.rotation.x;
  double qy = tf_stamp.transform.rotation.y;
  double qz = tf_stamp.transform.rotation.z;
  double qw = tf_stamp.transform.rotation.w;
  double yaw = std::atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz));
  double cos_y = std::cos(yaw);
  double sin_y = std::sin(yaw);

  double origin_x = grid->info.origin.position.x;
  double origin_y = grid->info.origin.position.y;
  double res = grid->info.resolution;
  unsigned int width = grid->info.width;
  unsigned int height = grid->info.height;

  // Safely clamp active bounding indices to costmap dimension limits
  int c_min_i = std::max(0, min_i);
  int c_min_j = std::max(0, min_j);
  int c_max_i = std::min(static_cast<int>(getSizeInCellsX()), max_i);
  int c_max_j = std::min(static_cast<int>(getSizeInCellsY()), max_j);

  if (c_min_i >= c_max_i || c_min_j >= c_max_j) {
    return;
  }

  // Reset strategy:
  // - rolling=true  (local costmap):  clear stale marks so controller is never frozen
  //                                   by old obstacle positions from past camera poses.
  // - rolling=false (global costmap): accumulate — planner remembers every obstacle
  //                                   ever detected, preventing routes through known hazards
  //                                   even when the camera is no longer looking at them.
  if (rolling_) {
    resetMap(static_cast<unsigned int>(c_min_i), static_cast<unsigned int>(c_min_j),
             static_cast<unsigned int>(c_max_i), static_cast<unsigned int>(c_max_j));
  }

  for (unsigned int gy = 0; gy < height; ++gy) {
    for (unsigned int gx = 0; gx < width; ++gx) {
      int8_t raw_val = grid->data[gy * width + gx];
      if (raw_val < 0) {
        continue;  // Unknown or sky — leave as FREE_SPACE (already cleared above)
      }

      // Local ground coordinate in sensor frame (base_footprint)
      double lx = origin_x + (static_cast<double>(gx) + 0.5) * res;
      double ly = origin_y + (static_cast<double>(gy) + 0.5) * res;

      // Transform to world frame (map or odom)
      double wx = tx + (lx * cos_y - ly * sin_y);
      double wy = ty + (lx * sin_y + ly * cos_y);

      unsigned int mx, my;
      if (!worldToMap(wx, wy, mx, my)) {
        continue;
      }

      // Map raw semantic class / occupancy to graded cost
      unsigned char cost = nav2_costmap_2d::FREE_SPACE;
      if (raw_val == 0) {
        cost = nav2_costmap_2d::FREE_SPACE;  // Smooth dirt trail
      } else if (raw_val <= 30) {
        cost = static_cast<unsigned char>(std::min(253.0, 35.0 * traversability_weight_));   // Grass
      } else if (raw_val <= 75) {
        cost = static_cast<unsigned char>(std::min(253.0, 130.0 * traversability_weight_));  // Bush / rough
      } else {
        cost = nav2_costmap_2d::LETHAL_OBSTACLE;  // Solid boulder / obstacle (254)
      }

      setCost(mx, my, cost);
    }
  }

  // Transfer layer costs onto master costmap in the safe active bounding window
  updateWithTrueOverwrite(master_grid, c_min_i, c_min_j, c_max_i, c_max_j);
}

void TraversabilityLayer::reset()
{
  std::lock_guard<std::mutex> lock(data_mutex_);
  latest_grid_ = nullptr;
  new_data_ = false;
  current_ = true;
}

}  // namespace ugv_nav2
