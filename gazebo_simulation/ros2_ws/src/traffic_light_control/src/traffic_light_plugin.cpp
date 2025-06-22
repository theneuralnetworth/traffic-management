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

namespace gazebo
{
  class TrafficLightPlugin : public ModelPlugin
  {
  public:
    void Load(physics::ModelPtr model, sdf::ElementPtr sdf) override
    {
      this->model_ = model;
      this->world_name_ = model->GetWorld()->Name();
      this->model_name_ = model->GetName();  // "stop_light"
      this->link_name_  = "link";

      // Set up Gazebo transport
      this->gz_node_ = transport::NodePtr(new transport::Node());
      this->gz_node_->Init(this->world_name_);
      this->vis_pub_ = this->gz_node_->Advertise<msgs::Visual>("~/visual");

      // Create ROS 2 node & sub
      this->ros_node_ = gazebo_ros::Node::Get(sdf, "traffic_light_node");
      std::string topic = "/stop_light/color";
      if (sdf->HasElement("rosTopic"))
        topic = sdf->Get<std::string>("rosTopic");
      this->sub_ = this->ros_node_->create_subscription<std_msgs::msg::String>(
        topic, 10,
        std::bind(&TrafficLightPlugin::OnRosMsg, this, std::placeholders::_1));

      RCLCPP_INFO(this->ros_node_->get_logger(), "TrafficLightPlugin loaded");
    }

  private:
    void OnRosMsg(const std_msgs::msg::String::SharedPtr msg)
    {
      auto color = msg->data; // "red", "yellow", "green", or "none"
      RCLCPP_INFO(this->ros_node_->get_logger(), "Received color '%s'", color.c_str());

      const std::unordered_map<std::string, std::string> names = {
        {"red",    model_name_ + "::" + link_name_ + "::red"},
        {"yellow", model_name_ + "::" + link_name_ + "::yellow"},
        {"green",  model_name_ + "::" + link_name_ + "::green"},
      };

      // First turn all off (visibility=false)
      for (auto const &p : names)
      {
        msgs::Visual vis_msg;
        vis_msg.set_name(p.second);
        vis_msg.set_parent_name(model_name_ + "::" + link_name_);
        vis_msg.set_visible(false);
        this->vis_pub_->Publish(vis_msg);
      }

      // Then if color is one of the keys, turn that one on
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
  };

  GZ_REGISTER_MODEL_PLUGIN(TrafficLightPlugin)
}
