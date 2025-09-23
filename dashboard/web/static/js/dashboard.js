// CollegeAdvisor Dashboard JavaScript

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
});