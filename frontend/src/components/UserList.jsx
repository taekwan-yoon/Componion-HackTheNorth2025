import React from "react";
import "./UserList.css";

const UserList = ({ users, currentUser, isMaster = false }) => {
  const formatJoinTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const isCurrentUser = (user) => {
    return currentUser && user.user_id === currentUser.user_id;
  };

  return (
    <div className="user-list">
      <div className="user-list-header">
        <h3>Session Participants</h3>
        <span className="user-count">
          {users.filter((user) => !user.is_master).length}
        </span>
      </div>

      <div className="users-container">
        {users.filter((user) => !user.is_master).length === 0 && !isMaster ? (
          <div className="no-users">
            <p>No participants yet</p>
          </div>
        ) : (
          <div className="users">
            {users
              .filter((user) => !user.display_name?.includes("Master"))
              .map((user) => (
                <div
                  key={user.user_id}
                  className={`user-item ${
                    isCurrentUser(user) ? "current-user" : ""
                  }`}
                >
                  <div className="user-avatar">
                    {user.display_name?.charAt(0) || "?"}
                  </div>
                  <div className="user-info">
                    <div className="user-name">
                      {user.display_name || "Unknown User"}
                      {isCurrentUser(user) && (
                        <span className="you-badge">You</span>
                      )}
                    </div>
                    <div className="user-joined">
                      Joined {formatJoinTime(user.joined_at)}
                    </div>
                  </div>
                  <div className="user-status">
                    <span className="online-indicator">🟢</span>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserList;
