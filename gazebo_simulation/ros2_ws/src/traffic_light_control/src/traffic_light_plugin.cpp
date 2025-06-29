#include <memory>
#include <string>
#include <unordered_map>

#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/transport/transport.hh>
#include <gazebo/msgs/msgs.hh>

#include <gazebo_ros/node.hpp>
#include <rclcpp/rclcpp.hpp>
#include "traffic_light_control/msg/light_command.hpp"

namespace gazebo
{
  class TrafficLightPlugin : public ModelPlugin
  {
  public:
    void Load(physics::ModelPtr model, sdf::ElementPtr sdf) override
    {
      this->model_ = model;
      this->world_name_ = model->GetWorld()->Name();
      this->model_name_ = model->GetName(); // e.g. stop_light_0
      this->link_name_  = "link";

      // Get traffic light ID from SDF
      if (sdf->HasElement("traffic_light_id"))
        this->light_id_ = sdf->Get<int>("traffic_light_id");
      else
        this->light_id_ = -1;

      // Set up Gazebo transport
      this->gz_node_ = transport::NodePtr(new transport::Node());
      this->gz_node_->Init(this->world_name_);
      this->vis_pub_ = this->gz_node_->Advertise<msgs::Visual>("~/visual");

      // ROS 2 node
      std::string node_name = this->model_name_ + "_node";
      this->ros_node_ = gazebo_ros::Node::Get(sdf, node_name);

      // Subscribe to LightCommand messages
      this->sub_ = this->ros_node_->create_subscription<
        traffic_light_control::msg::LightCommand>(
        "/light_commands", 10,
        std::bind(&TrafficLightPlugin::OnRosMsg, this, std::placeholders::_1)
      );

      RCLCPP_INFO(
        this->ros_node_->get_logger(),
        "TrafficLightPlugin loaded for model '%s' with id %d",
        this->model_name_.c_str(), this->light_id_
      );
    }

  private:
    void OnRosMsg(const traffic_light_control::msg::LightCommand::SharedPtr msg)
    {
      // Parse the incoming command
      int msg_id = std::stoi(msg->traffic_light_id);
      if (msg_id != this->light_id_)
        return;  // not for this light

      std::string color = msg->new_state;
      RCLCPP_INFO(
        this->ros_node_->get_logger(),
        "Changing light %d to %s", msg_id, color.c_str()
      );

      const std::unordered_map<std::string, std::string> names = {
        {"red",    this->model_name_ + "::" + this->link_name_ + "::red"},
        {"yellow", this->model_name_ + "::" + this->link_name_ + "::yellow"},
        {"green",  this->model_name_ + "::" + this->link_name_ + "::green"},
      };

      // Turn all lights off
      for (auto const &p : names)
      {
        msgs::Visual off_msg;
        off_msg.set_name(p.second);
        off_msg.set_parent_name(this->model_name_ + "::" + this->link_name_);
        off_msg.set_visible(false);
        this->vis_pub_->Publish(off_msg);
      }

      // Turn the requested light on
      auto it = names.find(color);
      if (it != names.end())
      {
        msgs::Visual on_msg;
        on_msg.set_name(it->second);
        on_msg.set_parent_name(this->model_name_ + "::" + this->link_name_);
        on_msg.set_visible(true);
        this->vis_pub_->Publish(on_msg);
      }
    }

    // Gazebo model and transport
    physics::ModelPtr model_;
    std::string world_name_;
    std::string model_name_;
    std::string link_name_;
    transport::NodePtr gz_node_;
    transport::PublisherPtr vis_pub_;

    // ROS 2 node and subscription
    std::shared_ptr<rclcpp::Node> ros_node_;
    rclcpp::Subscription<traffic_light_control::msg::LightCommand>::SharedPtr sub_;

    // Traffic light identifier
    int light_id_;
  };

  GZ_REGISTER_MODEL_PLUGIN(TrafficLightPlugin)
}
