#!/usr/bin/env python3
"""
Analytics Dashboard Deployment Script

This script deploys a web-based analytics dashboard for monitoring the CollegeAdvisor data pipeline.
"""

import os
import sys
import json
import yaml
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """Analytics dashboard for CollegeAdvisor data pipeline."""
    
    def __init__(self):
        self.dashboard_dir = project_root / "dashboard" / "web"
        self.static_dir = self.dashboard_dir / "static"
        self.templates_dir = self.dashboard_dir / "templates"
    
    def create_dashboard_structure(self):
        """Create dashboard directory structure."""
        logger.info("Creating dashboard directory structure...")
        
        # Create directories
        directories = [
            self.dashboard_dir,
            self.static_dir / "css",
            self.static_dir / "js",
            self.static_dir / "images",
            self.templates_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
    
    def create_dashboard_html(self):
        """Create main dashboard HTML template."""
        logger.info("Creating dashboard HTML template...")
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CollegeAdvisor Data Pipeline Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/dashboard.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="fas fa-chart-line me-2"></i>
                CollegeAdvisor Data Pipeline
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text" id="last-updated">
                    Last Updated: <span id="timestamp">--</span>
                </span>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- System Health Overview -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-heartbeat me-2"></i>
                            System Health Overview
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="health-metric">
                                    <div class="metric-value" id="overall-health">--</div>
                                    <div class="metric-label">Overall Health</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="health-metric">
                                    <div class="metric-value" id="cpu-usage">--</div>
                                    <div class="metric-label">CPU Usage</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="health-metric">
                                    <div class="metric-value" id="memory-usage">--</div>
                                    <div class="metric-label">Memory Usage</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="health-metric">
                                    <div class="metric-value" id="disk-usage">--</div>
                                    <div class="metric-label">Disk Usage</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Quality Metrics -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-check-circle me-2"></i>
                            Data Quality Metrics
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="quality-chart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-database me-2"></i>
                            Data Collection Status
                        </h5>
                    </div>
                    <div class="card-body">
                        <div id="collection-status">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pipeline Performance -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-tachometer-alt me-2"></i>
                            Pipeline Performance
                        </h5>
                    </div>
                    <div class="card-body">
                        <canvas id="performance-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Alerts -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Recent Alerts
                        </h5>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>'''
        
        html_file = self.templates_dir / "dashboard.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"✅ Created dashboard HTML: {html_file}")
    
    def create_dashboard_css(self):
        """Create dashboard CSS styles."""
        logger.info("Creating dashboard CSS...")
        
        css_content = '''/* CollegeAdvisor Dashboard Styles */

body {
    background-color: #f8f9fa;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.card {
    border: none;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border-radius: 0.5rem;
}

.card-header {
    background-color: #fff;
    border-bottom: 1px solid #dee2e6;
    border-radius: 0.5rem 0.5rem 0 0 !important;
}

.health-metric {
    text-align: center;
    padding: 1rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #28a745;
}

.metric-value.warning {
    color: #ffc107;
}

.metric-value.danger {
    color: #dc3545;
}

.metric-label {
    font-size: 0.875rem;
    color: #6c757d;
    margin-top: 0.5rem;
}

.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-healthy {
    background-color: #28a745;
}

.status-warning {
    background-color: #ffc107;
}

.status-error {
    background-color: #dc3545;
}

.alert-item {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0.375rem;
    border-left: 4px solid;
}

.alert-critical {
    background-color: #f8d7da;
    border-left-color: #dc3545;
}

.alert-high {
    background-color: #fff3cd;
    border-left-color: #ffc107;
}

.alert-medium {
    background-color: #d1ecf1;
    border-left-color: #17a2b8;
}

.alert-low {
    background-color: #d4edda;
    border-left-color: #28a745;
}

.chart-container {
    position: relative;
    height: 300px;
}

#last-updated {
    font-size: 0.875rem;
}

.navbar-brand {
    font-weight: 600;
}

.collection-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}

.collection-item:last-child {
    border-bottom: none;
}

.collection-name {
    font-weight: 500;
}

.collection-stats {
    font-size: 0.875rem;
    color: #6c757d;
}'''
        
        css_file = self.static_dir / "css" / "dashboard.css"
        with open(css_file, 'w') as f:
            f.write(css_content)
        
        logger.info(f"✅ Created dashboard CSS: {css_file}")
    
    def create_dashboard_js(self):
        """Create dashboard JavaScript."""
        logger.info("Creating dashboard JavaScript...")
        
        js_content = '''// CollegeAdvisor Dashboard JavaScript

class Dashboard {
    constructor() {
        this.charts = {};
        this.updateInterval = 30000; // 30 seconds
        this.init();
    }

    init() {
        this.createCharts();
        this.loadData();
        this.startAutoUpdate();
    }

    createCharts() {
        // Data Quality Chart
        const qualityCtx = document.getElementById('quality-chart').getContext('2d');
        this.charts.quality = new Chart(qualityCtx, {
            type: 'radar',
            data: {
                labels: ['Completeness', 'Consistency', 'Accuracy', 'Timeliness', 'Validity', 'Uniqueness'],
                datasets: [{
                    label: 'Quality Score',
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(40, 167, 69, 0.2)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    pointBackgroundColor: 'rgba(40, 167, 69, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(40, 167, 69, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });

        // Performance Chart
        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
        this.charts.performance = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Health Score',
                    data: [],
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }, {
                    label: 'CPU Usage',
                    data: [],
                    borderColor: 'rgba(255, 193, 7, 1)',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory Usage',
                    data: [],
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    async loadData() {
        try {
            // Load health data
            const healthData = await this.fetchHealthData();
            this.updateHealthMetrics(healthData);

            // Load quality data
            const qualityData = await this.fetchQualityData();
            this.updateQualityChart(qualityData);

            // Load collection status
            const collectionData = await this.fetchCollectionData();
            this.updateCollectionStatus(collectionData);

            // Load alerts
            const alertsData = await this.fetchAlertsData();
            this.updateAlerts(alertsData);

            // Update timestamp
            document.getElementById('timestamp').textContent = new Date().toLocaleString();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    async fetchHealthData() {
        // Mock data - replace with actual API call
        return {
            overall_score: 85.5,
            status: 'good',
            system: {
                cpu_percent: 45.2,
                memory_percent: 62.8,
                disk_percent: 34.1
            }
        };
    }

    async fetchQualityData() {
        // Mock data - replace with actual API call
        return {
            completeness: 0.95,
            consistency: 0.88,
            accuracy: 0.92,
            timeliness: 0.85,
            validity: 0.97,
            uniqueness: 0.94
        };
    }

    async fetchCollectionData() {
        // Mock data - replace with actual API call
        return [
            { name: 'College Scorecard', status: 'healthy', records: 15420, last_update: '2 hours ago' },
            { name: 'Social Media', status: 'healthy', records: 8932, last_update: '15 minutes ago' },
            { name: 'Authentication Events', status: 'healthy', records: 45123, last_update: '1 minute ago' },
            { name: 'User Profiles', status: 'warning', records: 12456, last_update: '6 hours ago' }
        ];
    }

    async fetchAlertsData() {
        // Mock data - replace with actual API call
        return [
            {
                severity: 'medium',
                message: 'Data quality threshold violation in user_profiles dataset',
                timestamp: '2024-01-15 14:30:00'
            },
            {
                severity: 'low',
                message: 'Training data generation completed successfully',
                timestamp: '2024-01-15 14:25:00'
            }
        ];
    }

    updateHealthMetrics(data) {
        const overallHealth = document.getElementById('overall-health');
        const cpuUsage = document.getElementById('cpu-usage');
        const memoryUsage = document.getElementById('memory-usage');
        const diskUsage = document.getElementById('disk-usage');

        overallHealth.textContent = `${data.overall_score.toFixed(1)}%`;
        overallHealth.className = `metric-value ${this.getHealthClass(data.overall_score)}`;

        cpuUsage.textContent = `${data.system.cpu_percent.toFixed(1)}%`;
        cpuUsage.className = `metric-value ${this.getUsageClass(data.system.cpu_percent)}`;

        memoryUsage.textContent = `${data.system.memory_percent.toFixed(1)}%`;
        memoryUsage.className = `metric-value ${this.getUsageClass(data.system.memory_percent)}`;

        diskUsage.textContent = `${data.system.disk_percent.toFixed(1)}%`;
        diskUsage.className = `metric-value ${this.getUsageClass(data.system.disk_percent)}`;
    }

    updateQualityChart(data) {
        const values = [
            data.completeness,
            data.consistency,
            data.accuracy,
            data.timeliness,
            data.validity,
            data.uniqueness
        ];

        this.charts.quality.data.datasets[0].data = values;
        this.charts.quality.update();
    }

    updateCollectionStatus(data) {
        const container = document.getElementById('collection-status');
        container.innerHTML = '';

        data.forEach(item => {
            const statusClass = `status-${item.status === 'healthy' ? 'healthy' : item.status === 'warning' ? 'warning' : 'error'}`;
            
            const itemElement = document.createElement('div');
            itemElement.className = 'collection-item';
            itemElement.innerHTML = `
                <div>
                    <span class="status-indicator ${statusClass}"></span>
                    <span class="collection-name">${item.name}</span>
                </div>
                <div class="collection-stats">
                    ${item.records.toLocaleString()} records | ${item.last_update}
                </div>
            `;
            
            container.appendChild(itemElement);
        });
    }

    updateAlerts(data) {
        const container = document.getElementById('alerts-container');
        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent alerts</p>';
            return;
        }

        data.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert-item alert-${alert.severity}`;
            alertElement.innerHTML = `
                <div class="d-flex justify-content-between">
                    <span>${alert.message}</span>
                    <small class="text-muted">${alert.timestamp}</small>
                </div>
            `;
            
            container.appendChild(alertElement);
        });
    }

    getHealthClass(score) {
        if (score >= 80) return '';
        if (score >= 60) return 'warning';
        return 'danger';
    }

    getUsageClass(usage) {
        if (usage < 70) return '';
        if (usage < 85) return 'warning';
        return 'danger';
    }

    startAutoUpdate() {
        setInterval(() => {
            this.loadData();
        }, this.updateInterval);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});'''
        
        js_file = self.static_dir / "js" / "dashboard.js"
        with open(js_file, 'w') as f:
            f.write(js_content)
        
        logger.info(f"✅ Created dashboard JavaScript: {js_file}")
    
    def create_flask_app(self):
        """Create Flask application for serving the dashboard."""
        logger.info("Creating Flask application...")
        
        app_content = '''#!/usr/bin/env python3
"""
Flask application for CollegeAdvisor Analytics Dashboard
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

@app.route('/')
def dashboard():
    """Serve the main dashboard."""
    return render_template('dashboard.html')

@app.route('/api/health')
def api_health():
    """API endpoint for health data."""
    # TODO: Implement actual health data retrieval
    return jsonify({
        'overall_score': 85.5,
        'status': 'good',
        'system': {
            'cpu_percent': 45.2,
            'memory_percent': 62.8,
            'disk_percent': 34.1
        }
    })

@app.route('/api/quality')
def api_quality():
    """API endpoint for quality data."""
    # TODO: Implement actual quality data retrieval
    return jsonify({
        'completeness': 0.95,
        'consistency': 0.88,
        'accuracy': 0.92,
        'timeliness': 0.85,
        'validity': 0.97,
        'uniqueness': 0.94
    })

@app.route('/api/collection')
def api_collection():
    """API endpoint for collection status."""
    # TODO: Implement actual collection data retrieval
    return jsonify([
        {'name': 'College Scorecard', 'status': 'healthy', 'records': 15420, 'last_update': '2 hours ago'},
        {'name': 'Social Media', 'status': 'healthy', 'records': 8932, 'last_update': '15 minutes ago'},
        {'name': 'Authentication Events', 'status': 'healthy', 'records': 45123, 'last_update': '1 minute ago'},
        {'name': 'User Profiles', 'status': 'warning', 'records': 12456, 'last_update': '6 hours ago'}
    ])

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts data."""
    # TODO: Implement actual alerts data retrieval
    return jsonify([
        {
            'severity': 'medium',
            'message': 'Data quality threshold violation in user_profiles dataset',
            'timestamp': '2024-01-15 14:30:00'
        },
        {
            'severity': 'low',
            'message': 'Training data generation completed successfully',
            'timestamp': '2024-01-15 14:25:00'
        }
    ])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)'''
        
        app_file = self.dashboard_dir / "app.py"
        with open(app_file, 'w') as f:
            f.write(app_content)
        
        logger.info(f"✅ Created Flask application: {app_file}")
    
    def deploy_dashboard(self):
        """Deploy the complete analytics dashboard."""
        logger.info("Deploying analytics dashboard...")
        
        # Create all dashboard components
        self.create_dashboard_structure()
        self.create_dashboard_html()
        self.create_dashboard_css()
        self.create_dashboard_js()
        self.create_flask_app()
        
        # Create requirements file for dashboard
        requirements_content = '''Flask==2.3.3
Jinja2==3.1.2
Werkzeug==2.3.7
'''
        
        requirements_file = self.dashboard_dir / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        
        logger.info(f"✅ Created dashboard requirements: {requirements_file}")
        
        # Create startup script
        startup_content = '''#!/bin/bash
# Analytics Dashboard Startup Script

echo "🚀 Starting CollegeAdvisor Analytics Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start the dashboard
echo "Starting dashboard on http://localhost:5000"
python app.py'''
        
        startup_file = self.dashboard_dir / "start_dashboard.sh"
        with open(startup_file, 'w') as f:
            f.write(startup_content)
        
        # Make startup script executable
        os.chmod(startup_file, 0o755)
        
        logger.info(f"✅ Created startup script: {startup_file}")
        
        return True


def main():
    """Main function to deploy analytics dashboard."""
    print("📊 CollegeAdvisor Analytics Dashboard Deployment")
    print("=" * 60)
    
    dashboard = AnalyticsDashboard()
    
    try:
        success = dashboard.deploy_dashboard()
        
        if success:
            print("\n🎉 Analytics dashboard deployed successfully!")
            print("\nTo start the dashboard:")
            print(f"  cd {dashboard.dashboard_dir}")
            print("  ./start_dashboard.sh")
            print("\nDashboard will be available at: http://localhost:5000")
            return 0
        else:
            print("\n❌ Dashboard deployment failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Dashboard deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
