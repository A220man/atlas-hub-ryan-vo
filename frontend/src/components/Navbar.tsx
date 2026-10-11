import React from "react";
import { useAuth } from "../context/AuthContext.tsx";

interface NavbarProps {
  onOpenCreate: () => void;
  onNavigateHome: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenCreate, onNavigateHome }) => {
  const { user, loginDemo, logout, hasRole } = useAuth();

  const handleRoleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const role = e.target.value;
    await loginDemo(role);
  };

  return (
    <header className="navbar">
      <div className="navbar-brand" onClick={onNavigateHome} style={{ cursor: "pointer" }}>
        <div className="brand-logo">A</div>
        <div>
          <div className="brand-title">Atlas Hub</div>
          <div className="brand-subtitle">AI Slide Synthesis & Alignment</div>
        </div>
      </div>

      <div className="navbar-actions">
        {hasRole("analyst") && (
          <button className="btn btn-primary" onClick={onOpenCreate}>
            + Synthesize Deck
          </button>
        )}

        <div className="role-switcher">
          <label htmlFor="role-select" className="role-label">Role:</label>
          <select
            id="role-select"
            className="select-input"
            value={user?.roles[0] || "analyst"}
            onChange={handleRoleChange}
          >
            <option value="viewer">Viewer</option>
            <option value="analyst">Analyst</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        {user && (
          <div className="user-profile">
            <span className="user-badge">{user.roles[0]}</span>
            <span className="user-email">{user.email}</span>
            <button className="btn btn-outline btn-sm" onClick={logout}>
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
