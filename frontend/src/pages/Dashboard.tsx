import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiService, Image as ImageType } from "../services/api";
import "./Dashboard.css";

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [images, setImages] = useState<ImageType[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }

    loadData();
  }, [user, navigate]);

  const loadData = async () => {
    try {
      const [dashboardData, imagesData] = await Promise.all([
        apiService.getDashboard(),
        apiService.listImages(),
      ]);
      setDashboard(dashboardData);
      setImages(imagesData.images);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.uploadImage(file);
      setSuccess("Image uploaded successfully!");
      await loadData();
      e.target.value = "";
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!window.confirm("Delete this image?")) return;

    try {
      await apiService.deleteImage(imageId);
      setSuccess("Image deleted successfully!");
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>📸 Photo Vault</h1>
        <div className="user-info">
          <span>{user?.email}</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="dashboard-content">
        {/* Dashboard Stats */}
        {dashboard && (
          <div className="stats-section">
            <div className="stat-card">
              <h3>Total Images</h3>
              <p className="stat-value">{dashboard.total_images}</p>
            </div>
            <div className="stat-card">
              <h3>Storage Used</h3>
              <p className="stat-value">
                {dashboard.storage_used_gb.toFixed(2)} GB / {dashboard.storage_quota_gb} GB
              </p>
            </div>
            <div className="stat-card">
              <h3>Account Created</h3>
              <p className="stat-value">{new Date(dashboard.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div className="upload-section">
          <h2>Upload New Image</h2>
          <label className="upload-label">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            <span>{isUploading ? "Uploading..." : "Click to upload image"}</span>
          </label>
        </div>

        {/* Gallery */}
        <div className="gallery-section">
          <h2>Your Images ({images.length})</h2>
          {images.length === 0 ? (
            <p className="empty-gallery">No images yet. Upload your first image!</p>
          ) : (
            <div className="gallery-grid">
              {images.map((image) => (
                <div key={image.id} className="gallery-item">
                  <img
                    src={image.gcs_uri.replace("gs://", "https://storage.googleapis.com/")}
                    alt={image.filename}
                    onError={(e) => {
                      e.currentTarget.src =
                        "https://via.placeholder.com/200?text=Image+Not+Found";
                    }}
                  />
                  <div className="image-info">
                    <p className="filename">{image.filename}</p>
                    <p className="date">{new Date(image.created_at).toLocaleDateString()}</p>
                    <button
                      onClick={() => handleDeleteImage(image.id)}
                      className="delete-btn"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
