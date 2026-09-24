#ifndef UGV_NAV2__TRAVERSABILITY_LAYER_HPP_
#define UGV_NAV2__TRAVERSABILITY_LAYER_HPP_

#include <memory>
#include <mutex>
#include <string>

#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav2_costmap_2d/costmap_layer.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2_ros/buffer.h"

    namespace ugv_nav2 {

  /**
   * @class TraversabilityLayer
   * @brief Nav2 Costmap Layer plugin ingesting AI semantic terrain
   * traversability and projecting graded costs (Trail=0, Grass=35, Bush=130,
   * Hazard=254) into the master costmap for terrain-aware global path planning.
   */
  class TraversabilityLayer : public nav2_costmap_2d::CostmapLayer {
  public:
    TraversabilityLayer();
    virtual ~TraversabilityLayer();

    virtual void onInitialize() override;
    virtual void updateBounds(double robot_x, double robot_y, double robot_yaw,
                              double *min_x, double *min_y, double *max_x,
                              double *max_y) override;
    virtual void updateCosts(nav2_costmap_2d::Costmap2D &master_grid, int min_i,
                             int min_j, int max_i, int max_j) override;
    virtual void reset() override;
    virtual bool isClearable() override { return false; }

  protected:
    void
    incomingGridCallback(const nav_msgs::msg::OccupancyGrid::SharedPtr msg);

    std::string topic_name_;
    double traversability_weight_;
    bool rolling_; ///< If true: resetMap each cycle (local costmap responsive
                   ///< mode). If false: accumulate (global costmap planning
                   ///< memory mode).
    bool new_data_;

    std::mutex data_mutex_;
    nav_msgs::msg::OccupancyGrid::SharedPtr latest_grid_;
    rclcpp::Subscription<nav_msgs::msg::OccupancyGrid>::SharedPtr grid_sub_;
  };

} // namespace ugv_nav2

#endif // UGV_NAV2__TRAVERSABILITY_LAYER_HPP_
