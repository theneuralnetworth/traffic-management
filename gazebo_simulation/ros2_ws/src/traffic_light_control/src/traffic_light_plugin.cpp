#include <memory>
#include <string>
#include <unordered_map>

#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/transport/transport.hh>
#include <gazebo/msgs/msgs.hh>

#include <gazebo_ros/node.hpp>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <rclcpp/subscription.hpp>
#include <rclcpp/logger.hpp>

#include <sstream>

namespace gazebo
{
  class TrafficLightPlugin : public ModelPlugin
  {
  public:
    void Load(physics::ModelPtr model, sdf::ElementPtr sdf) override
    {
      this->model_ = model;
      this->world_name_ = model->GetWorld()->Name();
      this->model_name_ = model->GetName();  // e.g. stop_light_0
      this->link_name_  = "link";

      // Get traffic light ID from SDF
      if (sdf->HasElement("traffic_light_id"))
        this->light_id_ = sdf->Get<int>("traffic_light_id");
      else
        this->light_id_ = -1; // invalid ID

      // Set up Gazebo transport
      this->gz_node_ = transport::NodePtr(new transport::Node());
      this->gz_node_->Init(this->world_name_);
      this->vis_pub_ = this->gz_node_->Advertise<msgs::Visual>("~/visual");

      // ROS 2 node
      std::string node_name = this->model_name_ + "_node";
      this->ros_node_ = gazebo_ros::Node::Get(sdf, node_name);

      // Subscribe to common topic
      this->sub_ = this->ros_node_->create_subscription<std_msgs::msg::String>(
        "/light_commands", 10,
        std::bind(&TrafficLightPlugin::OnRosMsg, this, std::placeholders::_1));

      RCLCPP_INFO(this->ros_node_->get_logger(),
                  "TrafficLightPlugin loaded for %s with ID %d", 
                  this->model_name_.c_str(), this->light_id_);
    }

  private:
    void OnRosMsg(const std_msgs::msg::String::SharedPtr msg)
    {
      // Expect messages like "0,red" (id,color)
      std::istringstream ss(msg->data);
      std::string token;
      if (!std::getline(ss, token, ',')) return;
      int msg_id = std::stoi(token);

      std::string color;
      if (!std::getline(ss, color)) return;

      if (msg_id != this->light_id_)
        return;  // Not for this light

      RCLCPP_INFO(this->ros_node_->get_logger(),
                  "Changing light %d to %s", msg_id, color.c_str());

      const std::unordered_map<std::string, std::string> names = {
        {"red",    model_name_ + "::" + link_name_ + "::red"},
        {"yellow", model_name_ + "::" + link_name_ + "::yellow"},
        {"green",  model_name_ + "::" + link_name_ + "::green"},
      };

      // Turn all off
      for (auto const &p : names)
      {
        msgs::Visual vis_msg;
        vis_msg.set_name(p.second);
        vis_msg.set_parent_name(model_name_ + "::" + link_name_);
        vis_msg.set_visible(false);
        this->vis_pub_->Publish(vis_msg);
      }

      // Turn requested one on
      if (names.count(color))
      {
        msgs::Visual vis_msg;
        vis_msg.set_name(names.at(color));
        vis_msg.set_parent_name(model_name_ + "::" + link_name_);
        vis_msg.set_visible(true);
        this->vis_pub_->Publish(vis_msg);
      }
    }

    // Members
    physics::ModelPtr model_;
    std::string world_name_, model_name_, link_name_;
    transport::NodePtr gz_node_;
    transport::PublisherPtr vis_pub_;
    std::shared_ptr<rclcpp::Node> ros_node_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;
    int light_id_;
  };

  GZ_REGISTER_MODEL_PLUGIN(TrafficLightPlugin)
}
