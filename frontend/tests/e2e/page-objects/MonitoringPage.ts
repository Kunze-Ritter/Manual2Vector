import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export interface StageMetrics {
  stage_name: string;
  status: string;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  success_rate: number;
}

export interface HardwareMetrics {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
}

export interface AlertData {
  id: string;
  type: string;
  severity: string;
  message: string;
  created_at: string;
  acknowledged: boolean;
  metadata?: any;
}

/**
 * Page object for monitoring page
 */
export class MonitoringPage extends BasePage {
  // Selectors
  private readonly pageTitle = 'h1:has-text("System Monitoring")';
  private readonly overviewTab = '[data-testid="tab-overview"]';
  private readonly pipelineTab = '[data-testid="tab-pipeline"]';
  private readonly queueTab = '[data-testid="tab-queue"]';
  private readonly dataQualityTab = '[data-testid="tab-data-quality"]';
  private readonly alertsTab = '[data-testid="tab-alerts"]';
  private readonly pipelineStatusCard = '[data-testid="pipeline-status-card"]';
  private readonly queueCard = '[data-testid="queue-card"]';
  private readonly dataQualityCard = '[data-testid="data-quality-card"]';
  private readonly alertsCard = '[data-testid="alerts-card"]';
  private readonly systemMetrics = '[data-testid="system-metrics"]';
  private readonly alertItem = '[data-testid="alert-item"]';
  private readonly acknowledgeButton = '[data-testid="acknowledge-button"]';
  private readonly dismissButton = '[data-testid="dismiss-button"]';

  /**
   * Navigate to monitoring page
   */
  async navigate(): Promise<void> {
    await this.goto('/monitoring');
    await this.waitForSelector(this.pageTitle);
    await this.waitForWebSocketConnection();
  }

  /**
   * Switch to specific tab
   */
  async switchTab(tabName: string): Promise<void> {
    const tabSelector = `[data-testid="tab-${tabName.toLowerCase().replace(/\s+/g, '-')}"]`;
    await this.clickTestId(tabSelector.replace('[data-testid="', '').replace('"]', ''));
    
    // Wait for tab content to load
    await this.page.waitForTimeout(500);
  }

  /**
   * Get pipeline success rate from overview card
   */
  async getPipelineSuccessRate(): Promise<number> {
    await this.waitForSelector(this.pipelineStatusCard);
    const successRateElement = this.page.locator('[data-testid="metric-success-rate"]');
    const text = await successRateElement.textContent();
    
    // Extract percentage from text (e.g., "95.2%" -> 95.2)
    const match = text?.match(/(\d+\.?\d*)%/);
    return match ? parseFloat(match[1]) : 0;
  }

  /**
   * Get queue pending count from overview card
   */
  async getQueuePendingCount(): Promise<number> {
    await this.waitForSelector(this.queueCard);
    const pendingElement = this.page.locator('[data-testid="metric-pending"]');
    const text = await pendingElement.textContent();
    
    // Extract number from text
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Get active alerts count
   */
  async getActiveAlertsCount(): Promise<number> {
    await this.waitForSelector(this.alertsCard);
    const alertsElement = this.page.locator('[data-testid="metric-active-alerts"]');
    const text = await alertsElement.textContent();
    
    // Extract number from text
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Acknowledge alert by index
   */
  async acknowledgeAlert(index = 0): Promise<void> {
    // Switch to alerts tab if not already there
    await this.switchTab('alerts');
    
    // Get alert at specific index
    const alerts = this.page.locator(this.alertItem);
    const targetAlert = alerts.nth(index);
    
    // Click acknowledge button
    const acknowledgeBtn = targetAlert.locator(this.acknowledgeButton);
    const alertId = await targetAlert.getAttribute('data-alert-id');
    
    if (!alertId) {
      throw new Error('Alert ID not found');
    }
    
    // Wait for API response
    const [response] = await Promise.all([
      this.waitForAPIResponse(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, 'POST'),
      acknowledgeBtn.click()
    ]);
    
    // Verify success
    const responseData = await response.json();
    if (!responseData.success) {
      throw new Error('Failed to acknowledge alert');
    }
    
    // Wait for UI to update
    await this.page.waitForTimeout(1000);
  }

  /**
   * Dismiss alert by index
   */
  async dismissAlert(index = 0): Promise<void> {
    // Switch to alerts tab if not already there
    await this.switchTab('alerts');
    
    // Get alert at specific index
    const alerts = this.page.locator(this.alertItem);
    const targetAlert = alerts.nth(index);
    
    // Click dismiss button
    const dismissBtn = targetAlert.locator(this.dismissButton);
    const alertId = await targetAlert.getAttribute('data-alert-id');
    
    if (!alertId) {
      throw new Error('Alert ID not found');
    }
    
    // Wait for API response
    const [response] = await Promise.all([
      this.waitForAPIResponse(`/api/v1/monitoring/alerts/${alertId}`, 'DELETE'),
      dismissBtn.click()
    ]);
    
    // Verify success
    const responseData = await response.json();
    if (!responseData.success) {
      throw new Error('Failed to dismiss alert');
    }
    
    // Wait for UI to update
    await this.page.waitForTimeout(1000);
  }

  /**
   * Wait for WebSocket connection
   */
  async waitForWebSocketConnection(): Promise<void> {
    await this.page.waitForFunction(() => {
      return (window as any).__wsConnected === true;
    }, { timeout: 10000 });
  }

  /**
   * Wait for specific WebSocket message type
   */
  async waitForWebSocketMessage(messageType: string, timeout = 5000): Promise<any> {
    return this.page.evaluate(async ({ type, waitTime }) => {
      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          reject(new Error(`Timeout waiting for WebSocket message: ${type}`));
        }, waitTime);
        
        const handler = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === type) {
              clearTimeout(timeoutId);
              window.removeEventListener('message', handler);
              resolve(data);
            }
          } catch (error) {
            // Ignore parsing errors
          }
        };
        
        window.addEventListener('message', handler);
      });
    }, { type: messageType, waitTime: timeout });
  }

  /**
   * Force WebSocket reconnection
   */
  async forceWebSocketReconnect(): Promise<number> {
    // Close WebSocket connection
    await this.page.evaluate(() => {
      if ((window as any).testWebSocket) {
        (window as any).testWebSocket.close();
      }
    });
    
    // Wait for reconnection attempts
    await this.page.waitForFunction(() => {
      return (window as any).__wsReconnectAttempts > 0;
    }, { timeout: 15000 });
    
    // Get number of reconnection attempts
    const attempts = await this.page.evaluate(() => {
      return (window as any).__wsReconnectAttempts || 0;
    });
    
    return attempts;
  }

  /**
   * Get stage metrics from pipeline tab
   */
  async getStageMetrics(): Promise<StageMetrics[]> {
    await this.switchTab('pipeline');
    
    await this.waitForSelector('[data-testid="stage-metrics-table"]');
    const rows = this.page.locator('[data-testid="stage-row"]');
    const count = await rows.count();
    
    const metrics: StageMetrics[] = [];
    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const cells = await row.locator('td').allTextContents();
      
      if (cells.length >= 6) {
        metrics.push({
          stage_name: cells[0]?.trim() || '',
          status: cells[1]?.trim() || '',
          pending: parseInt(cells[2]?.trim() || '0', 10),
          processing: parseInt(cells[3]?.trim() || '0', 10),
          completed: parseInt(cells[4]?.trim() || '0', 10),
          failed: parseInt(cells[5]?.trim() || '0', 10),
          success_rate: parseFloat(cells[6]?.trim()?.replace('%', '') || '0')
        });
      }
    }
    
    return metrics;
  }

  /**
   * Get hardware metrics from system metrics widget
   */
  async getHardwareMetrics(): Promise<HardwareMetrics> {
    await this.waitForSelector(this.systemMetrics);
    
    const cpuElement = this.page.locator('[data-testid="metric-cpu"]');
    const ramElement = this.page.locator('[data-testid="metric-ram"]');
    
    const cpuText = await cpuElement.textContent();
    const ramText = await ramElement.textContent();
    
    // Parse CPU percentage (e.g., "45%" -> 45)
    const cpuMatch = cpuText?.match(/(\d+\.?\d*)%/);
    const cpuPercent = cpuMatch ? parseFloat(cpuMatch[1]) : 0;
    
    // Parse RAM usage (e.g., "8.2 GB / 16 GB (51%)" -> { used: 8.2, total: 16, percent: 51 })
    const ramMatch = ramText?.match(/(\d+\.?\d*)\s*GB\s*\/\s*(\d+\.?\d*)\s*GB\s*\((\d+\.?\d*)%\)/);
    const ramUsed = ramMatch ? parseFloat(ramMatch[1]) : 0;
    const ramTotal = ramMatch ? parseFloat(ramMatch[2]) : 0;
    const ramPercent = ramMatch ? parseFloat(ramMatch[3]) : 0;
    
    return {
      cpu_percent: cpuPercent,
      ram_percent: ramPercent,
      ram_used_gb: ramUsed,
      ram_total_gb: ramTotal
    };
  }

  /**
   * Get all alerts from alerts tab
   */
  async getAlerts(): Promise<AlertData[]> {
    await this.switchTab('alerts');
    
    const alerts = this.page.locator(this.alertItem);
    const count = await alerts.count();
    
    const alertData: AlertData[] = [];
    for (let i = 0; i < count; i++) {
      const alert = alerts.nth(i);
      
      const id = await alert.getAttribute('data-alert-id') || '';
      const type = await alert.locator('[data-testid="alert-type"]').textContent() || '';
      const severity = await alert.locator('[data-testid="alert-severity"]').textContent() || '';
      const message = await alert.locator('[data-testid="alert-message"]').textContent() || '';
      const createdAt = await alert.locator('[data-testid="alert-created-at"]').textContent() || '';
      const acknowledged = await alert.locator('[data-testid="alert-acknowledged"]').isVisible();
      
      alertData.push({
        id: id.trim(),
        type: type.trim(),
        severity: severity.trim().toLowerCase(),
        message: message.trim(),
        created_at: createdAt.trim(),
        acknowledged
      });
    }
    
    return alertData;
  }

  /**
   * Create test alert via API
   */
  async createTestAlert(type: string, severity: string, message: string): Promise<string> {
    const token = await this.page.evaluate(() => localStorage.getItem('access_token'));
    
    const response = await this.page.request.post('/api/v1/monitoring/alerts', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        type,
        severity: severity.toUpperCase(),
        message,
        metadata: { test: true }
      }
    });
    
    if (!response.ok()) {
      throw new Error('Failed to create test alert');
    }
    
    const responseData = await response.json();
    return responseData.data?.id || responseData.id;
  }

  /**
   * Verify monitoring page is loaded
   */
  async isLoaded(): Promise<boolean> {
    return await this.isElementVisible(this.pageTitle) &&
           await this.isElementVisible(this.overviewTab) &&
           await this.isElementVisible(this.pipelineStatusCard);
  }

  /**
   * Get queue metrics from queue tab
   */
  async getQueueMetrics(): Promise<any> {
    await this.switchTab('queue');
    
    await this.waitForSelector('[data-testid="queue-metrics"]');
    
    const pendingElement = this.page.locator('[data-testid="queue-pending"]');
    const processingElement = this.page.locator('[data-testid="queue-processing"]');
    const completedElement = this.page.locator('[data-testid="queue-completed"]');
    const failedElement = this.page.locator('[data-testid="queue-failed"]');
    
    return {
      pending: parseInt(await pendingElement.textContent() || '0', 10),
      processing: parseInt(await processingElement.textContent() || '0', 10),
      completed: parseInt(await completedElement.textContent() || '0', 10),
      failed: parseInt(await failedElement.textContent() || '0', 10)
    };
  }

  /**
   * Get data quality metrics from data quality tab
   */
  async getDataQualityMetrics(): Promise<any> {
    await this.switchTab('data-quality');
    
    await this.waitForSelector('[data-testid="data-quality-metrics"]');
    
    const totalDocsElement = this.page.locator('[data-testid="metric-total-documents"]');
    const processedDocsElement = this.page.locator('[data-testid="metric-processed-documents"]');
    const qualityScoreElement = this.page.locator('[data-testid="metric-quality-score"]');
    
    return {
      total_documents: parseInt(await totalDocsElement.textContent() || '0', 10),
      processed_documents: parseInt(await processedDocsElement.textContent() || '0', 10),
      quality_score: parseFloat((await qualityScoreElement.textContent() || '0').replace('%', ''))
    };
  }

  /**
   * Check if WebSocket is connected
   */
  async isWebSocketConnected(): Promise<boolean> {
    return this.page.evaluate(() => (window as any).__wsConnected === true);
  }

  /**
   * Get WebSocket connection status
   */
  async getWebSocketStatus(): Promise<string> {
    const status = await this.page.evaluate(() => (window as any).__wsStatus || 'unknown');
    return status;
  }

  /**
   * Wait for metrics to update (real-time)
   */
  async waitForMetricsUpdate(timeout = 10000): Promise<void> {
    // Wait for any WebSocket message that indicates metrics update
    await this.waitForWebSocketMessage('pipeline_update', timeout);
  }
}

export default MonitoringPage;
