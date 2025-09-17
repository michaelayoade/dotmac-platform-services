/**
 * API Behavior Tester
 * Enhanced mock testing utilities with entity flow validation
 */

import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export interface MockResponse {
  status: number;
  data: any;
  delay?: number;
  headers?: Record<string, string>;
  shouldFail?: boolean;
  failureRate?: number;
}

export interface EntityFlowStep {
  name: string;
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  expectedData?: any;
  expectedStatus?: number;
  validations?: ((response: any) => boolean)[];
}

export interface EntityFlow {
  name: string;
  description: string;
  steps: EntityFlowStep[];
  entities: string[];
  requiredPermissions?: string[];
}

export class APIBehaviorTester {
  private server: any;
  private requestLog: Array<{
    method: string;
    url: string;
    timestamp: number;
    body?: any;
    response?: any;
  }> = [];
  private mockConfigs: Map<string, MockResponse> = new Map();
  private entityFlows: Map<string, EntityFlow> = new Map();

  constructor() {
    this.server = setupServer();
  }

  /**
   * Generic mock and log utility
   */
  mockAndLog(endpoint: string, response: MockResponse): void {
    this.mockConfigs.set(endpoint, response);

    // Extract method and path from endpoint
    const [method, path] = endpoint.split(' ');
    const httpMethod = (method || 'GET').toUpperCase();

    const handler = http[httpMethod.toLowerCase() as keyof typeof http](path, async (info) => {
      const requestData = {
        method: httpMethod,
        url: info.request.url,
        timestamp: Date.now(),
        body: info.request.method !== 'GET' ? await info.request.json().catch(() => null) : null,
      };

      // Simulate failure rate if configured
      if (response.shouldFail || (response.failureRate && Math.random() < response.failureRate)) {
        const errorResponse = {
          error: 'Mock API failure',
          message: 'Simulated API failure for testing',
          timestamp: new Date().toISOString(),
        };

        this.requestLog.push({
          ...requestData,
          response: { status: 500, data: errorResponse },
        });

        return HttpResponse.json(errorResponse, {
          status: 500,
          headers: response.headers,
        });
      }

      // Add delay if configured
      if (response.delay) {
        await new Promise((resolve) => setTimeout(resolve, response.delay));
      }

      this.requestLog.push({
        ...requestData,
        response: { status: response.status, data: response.data },
      });

      return HttpResponse.json(response.data, {
        status: response.status,
        headers: response.headers,
      });
    });

    this.server.use(handler);
  }

  /**
   * Setup reseller-specific mocks
   */
  setupResellerMocks(): void {
    // Territory dashboard mocks
    this.mockAndLog('GET /api/reseller/territory/dashboard', {
      status: 200,
      data: {
        territories: [
          { id: '1', name: 'North Region', coverage: 87.5, leads: 45, customers: 123 },
          { id: '2', name: 'South Region', coverage: 72.3, leads: 38, customers: 89 },
        ],
        leads: [
          {
            id: 'lead-1',
            company: 'TechCorp',
            location: 'North',
            score: 85,
            priority: 'high',
            estimatedValue: 25000,
          },
          {
            id: 'lead-2',
            company: 'SmallBiz',
            location: 'South',
            score: 65,
            priority: 'medium',
            estimatedValue: 12000,
          },
        ],
        metrics: {
          territoryCoverage: '87.5%',
          activeLeads: '142',
          conversionRate: '24.8%',
          pipelineValue: '$1.2M',
        },
        charts: {
          'leads-by-region': [
            { name: 'North', leads: 45, value: 45 },
            { name: 'South', leads: 38, value: 38 },
            { name: 'East', leads: 32, value: 32 },
            { name: 'West', leads: 27, value: 27 },
          ],
          'conversion-funnel': [
            { stage: 'Leads', value: 100, count: 142 },
            { stage: 'Qualified', value: 65, count: 92 },
            { stage: 'Proposal', value: 35, count: 50 },
            { stage: 'Closed', value: 25, count: 35 },
          ],
        },
      },
      delay: 500,
    });

    // Sales pipeline mocks
    this.mockAndLog('GET /api/reseller/sales/deals', {
      status: 200,
      data: {
        data: [
          {
            id: 'deal-1',
            title: 'TechCorp ISP Setup',
            stage: 'leads',
            value: 25000,
            assignee: 'John Doe',
            dueDate: '2024-09-15',
            priority: 'high',
          },
          {
            id: 'deal-2',
            title: 'SmallBiz Internet',
            stage: 'qualified',
            value: 8500,
            assignee: 'Jane Smith',
            dueDate: '2024-09-20',
            priority: 'medium',
          },
        ],
        total: 47,
        pipeline: {
          leads: [{ id: 'lead-1', title: 'TechCorp ISP Setup', value: 25000, priority: 'high' }],
          qualified: [
            { id: 'qual-1', title: 'SmallBiz Internet', value: 8500, priority: 'medium' },
          ],
          proposal: [],
          negotiation: [],
          closedWon: [],
          closedLost: [],
        },
      },
    });

    // Projects mocks
    this.mockAndLog('GET /api/reseller/projects', {
      status: 200,
      data: {
        data: [
          {
            id: 'proj-1',
            name: 'Regional Network Expansion',
            partner: 'TechCorp',
            status: 'active',
            priority: 'high',
            completedMilestones: 5,
            totalMilestones: 8,
            startDate: '2024-01-15',
            targetDate: '2024-12-31',
            budget: 150000,
          },
          {
            id: 'proj-2',
            name: 'Small Business Package Launch',
            partner: 'NetSolutions',
            status: 'on-track',
            priority: 'medium',
            completedMilestones: 3,
            totalMilestones: 5,
            startDate: '2024-03-01',
            targetDate: '2024-10-15',
            budget: 75000,
          },
        ],
        total: 23,
      },
    });
  }

  /**
   * Setup technician-specific mocks
   */
  setupTechnicianMocks(): void {
    // Work orders mocks
    this.mockAndLog('GET /api/technician/work-orders', {
      status: 200,
      data: {
        data: [
          {
            id: 'wo-1',
            title: 'Internet Installation - TechCorp',
            customer: 'TechCorp Ltd',
            priority: 'high',
            status: 'assigned',
            scheduledDate: '2024-09-05',
            estimatedDuration: 240,
            location: '123 Business Ave, City',
          },
          {
            id: 'wo-2',
            title: 'Service Repair - Home User',
            customer: 'John Smith',
            priority: 'medium',
            status: 'in-progress',
            scheduledDate: '2024-09-04',
            estimatedDuration: 120,
            location: '456 Residential St, City',
          },
        ],
        total: 15,
      },
    });

    // Equipment inventory mocks
    this.mockAndLog('GET /api/technician/equipment', {
      status: 200,
      data: {
        assigned: [
          { id: 'eq-1', name: 'Router Model X', serialNumber: 'RTX001', status: 'available' },
          { id: 'eq-2', name: 'Modem Pro', serialNumber: 'MPR002', status: 'in-use' },
        ],
        summary: {
          available: 8,
          inUse: 5,
          maintenance: 2,
          total: 15,
        },
      },
    });

    // Time tracking mocks
    this.mockAndLog('GET /api/technician/time-entries', {
      status: 200,
      data: {
        entries: [
          {
            id: 'time-1',
            workOrderId: 'wo-1',
            startTime: '2024-09-04T09:00:00Z',
            endTime: '2024-09-04T13:30:00Z',
            duration: 270,
            description: 'Installation and configuration',
          },
        ],
        todayTotal: 270,
        weekTotal: 1850,
      },
    });
  }

  /**
   * Add entity flow validator
   */
  addEntityFlow(flow: EntityFlow): void {
    this.entityFlows.set(flow.name, flow);
  }

  /**
   * Validate complete entity flow
   */
  async validateEntityFlow(flowName: string): Promise<{
    success: boolean;
    results: Array<{
      step: string;
      success: boolean;
      error?: string;
      response?: any;
    }>;
  }> {
    const flow = this.entityFlows.get(flowName);
    if (!flow) {
      throw new Error(`Entity flow '${flowName}' not found`);
    }

    const results = [];
    let allSuccess = true;

    for (const step of flow.steps) {
      try {
        // Simulate API call
        const url = step.endpoint;
        const requestInit: RequestInit = {
          method: step.method,
          headers: { 'Content-Type': 'application/json' },
        };

        if (step.expectedData && ['POST', 'PUT', 'PATCH'].includes(step.method)) {
          requestInit.body = JSON.stringify(step.expectedData);
        }

        const response = await fetch(url, requestInit);
        const data = await response.json();

        // Validate response
        const stepSuccess = response.status === (step.expectedStatus || 200);

        // Run custom validations
        let validationSuccess = true;
        if (step.validations) {
          for (const validation of step.validations) {
            if (!validation(data)) {
              validationSuccess = false;
              break;
            }
          }
        }

        const success = stepSuccess && validationSuccess;
        if (!success) allSuccess = false;

        results.push({
          step: step.name,
          success,
          response: data,
          error: !success ? `Step failed: ${step.name}` : undefined,
        });
      } catch (error) {
        allSuccess = false;
        results.push({
          step: step.name,
          success: false,
          error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        });
      }
    }

    return { success: allSuccess, results };
  }

  /**
   * Start the mock server
   */
  start(): void {
    this.server.listen({ onUnhandledRequest: 'warn' });
  }

  /**
   * Stop the mock server
   */
  stop(): void {
    this.server.close();
  }

  /**
   * Reset all mocks and logs
   */
  reset(): void {
    this.server.resetHandlers();
    this.requestLog = [];
    this.mockConfigs.clear();
  }

  /**
   * Get request logs
   */
  getRequestLog(): typeof this.requestLog {
    return [...this.requestLog];
  }

  /**
   * Get request statistics
   */
  getRequestStats(): {
    totalRequests: number;
    successRate: number;
    averageResponseTime: number;
    endpointBreakdown: Record<string, number>;
  } {
    const total = this.requestLog.length;
    if (total === 0) {
      return {
        totalRequests: 0,
        successRate: 0,
        averageResponseTime: 0,
        endpointBreakdown: {},
      };
    }

    const successful = this.requestLog.filter(
      (r) => r.response?.status && r.response.status < 400
    ).length;

    const endpointCounts: Record<string, number> = {};
    this.requestLog.forEach((log) => {
      const endpoint = `${log.method} ${new URL(log.url).pathname}`;
      endpointCounts[endpoint] = (endpointCounts[endpoint] || 0) + 1;
    });

    return {
      totalRequests: total,
      successRate: (successful / total) * 100,
      averageResponseTime: 0, // Would need timing data
      endpointBreakdown: endpointCounts,
    };
  }

  /**
   * Validate mock response matches schema
   */
  validateResponseSchema(endpoint: string, schema: any): boolean {
    const config = this.mockConfigs.get(endpoint);
    if (!config) return false;

    try {
      // Basic schema validation - in real implementation would use Zod or similar
      return typeof config.data === typeof schema;
    } catch {
      return false;
    }
  }

  /**
   * Setup common entity flows
   */
  setupCommonEntityFlows(): void {
    // Customer lifecycle flow
    this.addEntityFlow({
      name: 'customer-lifecycle',
      description: 'Complete customer onboarding to service activation',
      entities: ['customer', 'service', 'billing'],
      steps: [
        {
          name: 'Create Customer',
          endpoint: '/api/customers',
          method: 'POST',
          expectedStatus: 201,
          expectedData: { name: 'Test Customer', email: 'test@example.com' },
          validations: [(data) => data.id !== undefined],
        },
        {
          name: 'Create Service',
          endpoint: '/api/services',
          method: 'POST',
          expectedStatus: 201,
          validations: [(data) => data.customerId !== undefined],
        },
        {
          name: 'Activate Service',
          endpoint: '/api/services/{id}/activate',
          method: 'PATCH',
          expectedStatus: 200,
          validations: [(data) => data.status === 'active'],
        },
      ],
    });

    // Sales pipeline flow
    this.addEntityFlow({
      name: 'sales-pipeline',
      description: 'Lead to closed deal progression',
      entities: ['lead', 'opportunity', 'deal'],
      steps: [
        {
          name: 'Create Lead',
          endpoint: '/api/reseller/leads',
          method: 'POST',
          expectedStatus: 201,
        },
        {
          name: 'Qualify Lead',
          endpoint: '/api/reseller/leads/{id}/qualify',
          method: 'PATCH',
          expectedStatus: 200,
        },
        {
          name: 'Convert to Deal',
          endpoint: '/api/reseller/deals',
          method: 'POST',
          expectedStatus: 201,
        },
        {
          name: 'Update Deal Stage',
          endpoint: '/api/reseller/deals/{id}',
          method: 'PATCH',
          expectedStatus: 200,
        },
      ],
    });
  }
}

// Export singleton instance
export const apiBehaviorTester = new APIBehaviorTester();
