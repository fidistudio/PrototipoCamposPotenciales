; Auto-generated. Do not edit!


(cl:in-package nav_apf_smach-msg)


;//! \htmlinclude NextWaypointFeedback.msg.html

(cl:defclass <NextWaypointFeedback> (roslisp-msg-protocol:ros-message)
  ((remaining_distance
    :reader remaining_distance
    :initarg :remaining_distance
    :type cl:float
    :initform 0.0)
   (f_attr
    :reader f_attr
    :initarg :f_attr
    :type geometry_msgs-msg:Vector3
    :initform (cl:make-instance 'geometry_msgs-msg:Vector3))
   (f_rep
    :reader f_rep
    :initarg :f_rep
    :type geometry_msgs-msg:Vector3
    :initform (cl:make-instance 'geometry_msgs-msg:Vector3))
   (debug_info
    :reader debug_info
    :initarg :debug_info
    :type cl:string
    :initform ""))
)

(cl:defclass NextWaypointFeedback (<NextWaypointFeedback>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <NextWaypointFeedback>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'NextWaypointFeedback)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name nav_apf_smach-msg:<NextWaypointFeedback> is deprecated: use nav_apf_smach-msg:NextWaypointFeedback instead.")))

(cl:ensure-generic-function 'remaining_distance-val :lambda-list '(m))
(cl:defmethod remaining_distance-val ((m <NextWaypointFeedback>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader nav_apf_smach-msg:remaining_distance-val is deprecated.  Use nav_apf_smach-msg:remaining_distance instead.")
  (remaining_distance m))

(cl:ensure-generic-function 'f_attr-val :lambda-list '(m))
(cl:defmethod f_attr-val ((m <NextWaypointFeedback>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader nav_apf_smach-msg:f_attr-val is deprecated.  Use nav_apf_smach-msg:f_attr instead.")
  (f_attr m))

(cl:ensure-generic-function 'f_rep-val :lambda-list '(m))
(cl:defmethod f_rep-val ((m <NextWaypointFeedback>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader nav_apf_smach-msg:f_rep-val is deprecated.  Use nav_apf_smach-msg:f_rep instead.")
  (f_rep m))

(cl:ensure-generic-function 'debug_info-val :lambda-list '(m))
(cl:defmethod debug_info-val ((m <NextWaypointFeedback>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader nav_apf_smach-msg:debug_info-val is deprecated.  Use nav_apf_smach-msg:debug_info instead.")
  (debug_info m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <NextWaypointFeedback>) ostream)
  "Serializes a message object of type '<NextWaypointFeedback>"
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'remaining_distance))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'f_attr) ostream)
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'f_rep) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'debug_info))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'debug_info))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <NextWaypointFeedback>) istream)
  "Deserializes a message object of type '<NextWaypointFeedback>"
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'remaining_distance) (roslisp-utils:decode-single-float-bits bits)))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'f_attr) istream)
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'f_rep) istream)
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'debug_info) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'debug_info) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<NextWaypointFeedback>)))
  "Returns string type for a message object of type '<NextWaypointFeedback>"
  "nav_apf_smach/NextWaypointFeedback")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'NextWaypointFeedback)))
  "Returns string type for a message object of type 'NextWaypointFeedback"
  "nav_apf_smach/NextWaypointFeedback")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<NextWaypointFeedback>)))
  "Returns md5sum for a message object of type '<NextWaypointFeedback>"
  "dd16aa403c54fc87081bcc540938af87")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'NextWaypointFeedback)))
  "Returns md5sum for a message object of type 'NextWaypointFeedback"
  "dd16aa403c54fc87081bcc540938af87")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<NextWaypointFeedback>)))
  "Returns full string definition for message of type '<NextWaypointFeedback>"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# Feedback~%float32 remaining_distance~%geometry_msgs/Vector3 f_attr~%geometry_msgs/Vector3 f_rep~%string debug_info~%~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'NextWaypointFeedback)))
  "Returns full string definition for message of type 'NextWaypointFeedback"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# Feedback~%float32 remaining_distance~%geometry_msgs/Vector3 f_attr~%geometry_msgs/Vector3 f_rep~%string debug_info~%~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <NextWaypointFeedback>))
  (cl:+ 0
     4
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'f_attr))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'f_rep))
     4 (cl:length (cl:slot-value msg 'debug_info))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <NextWaypointFeedback>))
  "Converts a ROS message object to a list"
  (cl:list 'NextWaypointFeedback
    (cl:cons ':remaining_distance (remaining_distance msg))
    (cl:cons ':f_attr (f_attr msg))
    (cl:cons ':f_rep (f_rep msg))
    (cl:cons ':debug_info (debug_info msg))
))
