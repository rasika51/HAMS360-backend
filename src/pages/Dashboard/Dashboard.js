import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('week');
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    totalAssets: 0,
    totalResources: 0,
    lowStockItems: [],
    recentUpdates: [],
    chartData: [],
    quickStats: {
      activeItems: 0,
      categories: 0
    }
  });

  // Fetch all dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch total assets
      const assetsResponse = await axios.get('http://localhost:5001/api/total-assets');
      // Fetch total resources
      const resourcesResponse = await axios.get('http://localhost:5001/api/total-resources');

      setDashboardData((prevData) => ({
        ...prevData,
        totalAssets: assetsResponse.data.totalAssets,
        totalResources: resourcesResponse.data.totalResources,
      }));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch chart data
  const fetchChartData = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/asset-timeline');
      setDashboardData((prevData) => ({
        ...prevData,
        chartData: response.data.chartData,
      }));
    } catch (error) {
      console.error('Error fetching asset timeline:', error);
    }
  };

  // Fetch low stock items
  const fetchLowStockItems = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/dashboard/low-stock');

      // Transform backend response to match frontend expectations
      const transformedItems = response.data.lowStockItems.map(item => ({
        id: item.id,
        name: item.assetName,       // Map assetName to name
        stockCount: item.stockCount,
        threshold: 10,              // Hardcode threshold since backend uses <10
        section: item.section,      // Preserve additional data if needed
        lastUpdated: item.lastUpdated
      }));

      setDashboardData((prevData) => ({
        ...prevData,
        lowStockItems: transformedItems,
      }));
    } catch (error) {
      console.error('Error fetching low stock items:', error);
    }
  };

  const fetchRecentUpdates = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/recent-updates');
      setDashboardData(prev => ({
        ...prev,
        recentUpdates: response.data.recentUpdates
      }));
    } catch (error) {
      console.error('Error fetching recent updates:', error);
    }
  };

  

  // Fetch all data on component mount
  useEffect(() => {
    fetchDashboardData();
    fetchChartData();
    fetchLowStockItems();
    fetchRecentUpdates(); 
  }, []);

  // Format date for display
  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Loading state
  if (loading) {
    return <div className="loading">Loading dashboard data...</div>;
  }


 
  

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Hospital Inventory Dashboard</h1>
        <div className="header-actions">
          <button className="refresh-btn" onClick={fetchDashboardData}>
            <i className="fas fa-sync"></i> Refresh
          </button>
        </div>
      </div>

      {/* Stats Container */}
      <div className="stats-container">
        <div className="dashboard-card total-assets">
          <div className="card-icon">
            <i className="fas fa-boxes"></i>
          </div>
          <div className="card-content">
            <h2>Total Assets</h2>
            <p className="number">{dashboardData.totalAssets}</p>
          </div>
        </div>

        <div className="dashboard-card resources" onClick={() => navigate('/resources')}>
          <div className="card-icon">
            <i className="fas fa-cubes"></i>
          </div>
          <div className="card-content">
            <h2>Total Resources</h2>
            <p className="number">{dashboardData.totalResources}</p>
          </div>
        </div>

        <div className="dashboard-card quick-stats">
          <div className="card-icon">
            <i className="fas fa-chart-pie"></i>
          </div>
          <div className="card-content">
            <h2>Quick Stats</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Active Items</span>
                <span className="stat-value">{dashboardData.quickStats.activeItems}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Categories</span>
                <span className="stat-value">{dashboardData.quickStats.categories}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Asset Timeline Chart */}
      <div className="dashboard-card graph-section">
        <div className="card-header">
          <h2>Asset Timeline</h2>
          <div className="time-controls">
            <button
              className={timeRange === 'week' ? 'active' : ''}
              onClick={() => setTimeRange('week')}
            >
              Week
            </button>
            <button
              className={timeRange === 'month' ? 'active' : ''}
              onClick={() => setTimeRange('month')}
            >
              Month
            </button>
            <button
              className={timeRange === 'year' ? 'active' : ''}
              onClick={() => setTimeRange('year')}
            >
              Year
            </button>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dashboardData.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#666"
            />
            <YAxis
              stroke="#666"
              label={{
                value: 'Total Assets',
                angle: -90,
                position: 'insideLeft'
              }}
            />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: 'none',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
              labelFormatter={(label) => `Date: ${formatDate(label)}`}
              formatter={(value) => [`Total Assets: ${value}`, '']}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="totalAssets"
              stroke="#4CAF50"
              strokeWidth={2}
              dot={{ strokeWidth: 2 }}
              name="Total Assets"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom Grid */}
      <div className="bottom-grid">
        {/* Low Stock Alert Section */}
        <div className="dashboard-card low-stock">
          <div className="card-header">
            <h2>Low Stock Alert</h2>
            <span className="alert-count">{dashboardData.lowStockItems.length} items</span>
          </div>
          <div className="alert-list">
            {dashboardData.lowStockItems.map((item) => (
              <div key={item.id} className="alert-item">
                <div className="item-info">
                  <span className="item-name">{item.name}</span>
                  <div className="progress-bar">
                    <div
                      className="progress"
                      style={{
                        width: `${(item.stockCount / 10) * 100}%` // Use hardcoded threshold 10
                      }}
                    ></div>
                  </div>
                </div>
                <span className="quantity">
                  {item.stockCount}/10
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Updates Section */}
        <div className="dashboard-card recent-updates">
          <div className="card-header">
            <h2>Recent Updates</h2>
            <button className="view-all" onClick={() => navigate('/recent-updates')}>
              View All
            </button>
          </div>
          <div className="updates-list">
            {dashboardData.recentUpdates.map((update) => (
              <div key={update.id} className="update-item">
                <div className="update-icon">
                  {update.action === 'Increased' ? '↑' : '↓'}
                </div>
                <div className="update-details">
                  <span className="item-name">{update.item}</span>
                  <span className="update-info">
                    {update.action} • {update.quantity} units • {update.date}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reports Section */}
        <div className="dashboard-card reports" onClick={() => navigate('/reports')}>
          <div className="card-content">
            <div className="report-icon">
              <i className="fas fa-file-alt"></i>
            </div>
            <h2>Generate Reports</h2>
            <p>Access detailed inventory reports and analytics</p>
            <button className="report-btn">View Reports</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;