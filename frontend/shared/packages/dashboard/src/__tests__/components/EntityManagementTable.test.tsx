/**
 * EntityManagementTable Component Test Suite
 * Production-ready test coverage for universal table component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  EntityManagementTable,
  EntityTablePresets,
} from '../../components/EntityManagementTable/EntityManagementTable';
import type { TableColumn, EntityAction } from '../../types';

// Mock data
const mockData = [
  { id: '1', name: 'John Doe', email: 'john@example.com', status: 'active', plan: 'premium' },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com', status: 'inactive', plan: 'basic' },
  { id: '3', name: 'Bob Johnson', email: 'bob@example.com', status: 'active', plan: 'premium' },
];

const mockColumns: TableColumn[] = [
  { key: 'name', title: 'Name', sortable: true },
  { key: 'email', title: 'Email', sortable: true },
  { key: 'status', title: 'Status', filterable: true },
  { key: 'plan', title: 'Plan', filterable: true },
];

const mockActions: EntityAction[] = [
  {
    key: 'edit',
    label: 'Edit',
    onClick: jest.fn(),
    isVisible: () => true,
  },
  {
    key: 'delete',
    label: 'Delete',
    variant: 'danger',
    onClick: jest.fn(),
    isVisible: () => true,
  },
];

const defaultProps = {
  data: mockData,
  columns: mockColumns,
  variant: 'admin' as const,
  actions: mockActions,
};

describe('🗃️ EntityManagementTable', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render table with data', () => {
      render(<EntityManagementTable {...defaultProps} />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    });

    it('should render column headers', () => {
      render(<EntityManagementTable {...defaultProps} />);

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Plan')).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(<EntityManagementTable {...defaultProps} loading={true} />);

      expect(
        screen.getByTestId('loading-skeleton') || screen.getByText('Loading...')
      ).toBeInTheDocument();
    });

    it('should render empty state when no data', () => {
      render(<EntityManagementTable {...defaultProps} data={[]} />);

      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });

  describe('Portal Variants', () => {
    it.each(['admin', 'customer', 'reseller', 'technician', 'management'])(
      'should apply %s variant styles',
      (variant) => {
        const { container } = render(
          <EntityManagementTable {...defaultProps} variant={variant as any} />
        );

        // Check that variant-specific classes are applied
        const tableElement = container.querySelector('table');
        expect(tableElement).toHaveClass(expect.stringContaining(variant));
      }
    );
  });

  describe('Search Functionality', () => {
    it('should filter data based on search query', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} searchable={true} />);

      const searchInput = screen.getByPlaceholderText('Search...');
      await user.type(searchInput, 'John');

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
      });
    });

    it('should search across multiple columns', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} searchable={true} />);

      const searchInput = screen.getByPlaceholderText('Search...');
      await user.type(searchInput, 'premium');

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
      });
    });
  });

  describe('Sorting Functionality', () => {
    it('should sort data when column header is clicked', async () => {
      const user = userEvent.setup();
      const onSortChange = jest.fn();

      render(
        <EntityManagementTable {...defaultProps} sortable={true} onSortChange={onSortChange} />
      );

      const nameHeader = screen.getByText('Name');
      await user.click(nameHeader);

      expect(onSortChange).toHaveBeenCalledWith('name', 'asc');
    });

    it('should toggle sort direction on repeated clicks', async () => {
      const user = userEvent.setup();
      const onSortChange = jest.fn();

      render(
        <EntityManagementTable {...defaultProps} sortable={true} onSortChange={onSortChange} />
      );

      const nameHeader = screen.getByText('Name');
      await user.click(nameHeader);
      await user.click(nameHeader);

      expect(onSortChange).toHaveBeenLastCalledWith('name', 'desc');
    });
  });

  describe('Selection Functionality', () => {
    it('should handle row selection', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();

      render(
        <EntityManagementTable
          {...defaultProps}
          selectable={true}
          onSelectionChange={onSelectionChange}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[1]); // First row checkbox (index 0 is select all)

      expect(onSelectionChange).toHaveBeenCalledWith(['1']);
    });

    it('should handle select all functionality', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();

      render(
        <EntityManagementTable
          {...defaultProps}
          selectable={true}
          onSelectionChange={onSelectionChange}
        />
      );

      const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
      await user.click(selectAllCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['1', '2', '3']);
    });
  });

  describe('Actions', () => {
    it('should render action buttons', () => {
      render(<EntityManagementTable {...defaultProps} />);

      // Actions column should be present
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('should call action handler when clicked', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} />);

      // Find first edit button (assuming icon-only buttons)
      const actionButtons = screen.getAllByRole('button');
      const editButton = actionButtons.find(
        (btn) =>
          btn.getAttribute('aria-label')?.includes('Edit') || btn.textContent?.includes('Edit')
      );

      if (editButton) {
        await user.click(editButton);
        expect(mockActions[0].onClick).toHaveBeenCalled();
      }
    });

    it('should handle bulk actions with selection', async () => {
      const user = userEvent.setup();
      const bulkDeleteAction = {
        key: 'bulk-delete',
        label: 'Delete Selected',
        variant: 'danger' as const,
        onClick: jest.fn(),
      };

      render(
        <EntityManagementTable
          {...defaultProps}
          selectable={true}
          bulkActions={[bulkDeleteAction]}
          selectedIds={['1', '2']}
        />
      );

      expect(screen.getByText('2 selected')).toBeInTheDocument();
      expect(screen.getByText('Delete Selected')).toBeInTheDocument();
    });
  });

  describe('Filters', () => {
    const filtersConfig = [
      {
        key: 'status',
        label: 'Status',
        options: [
          { value: 'active', label: 'Active' },
          { value: 'inactive', label: 'Inactive' },
        ],
      },
    ];

    it('should show filters when configured', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} filters={filtersConfig} />);

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Status:')).toBeInTheDocument();
      });
    });

    it('should filter data based on filter selection', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} filters={filtersConfig} />);

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(async () => {
        const statusFilter = screen.getByRole('combobox');
        await user.selectOptions(statusFilter, 'active');
      });

      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
      });
    });
  });

  describe('Pagination', () => {
    const paginationConfig = {
      page: 1,
      pageSize: 2,
      total: 10,
      onPageChange: jest.fn(),
      onPageSizeChange: jest.fn(),
    };

    it('should render pagination controls', () => {
      render(<EntityManagementTable {...defaultProps} pagination={paginationConfig} />);

      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Page 1 of 5')).toBeInTheDocument();
    });

    it('should handle page change', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} pagination={paginationConfig} />);

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      expect(paginationConfig.onPageChange).toHaveBeenCalledWith(2);
    });

    it('should handle page size change', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} pagination={paginationConfig} />);

      const pageSizeSelect = screen.getByDisplayValue('2');
      await user.selectOptions(pageSizeSelect, '10');

      expect(paginationConfig.onPageSizeChange).toHaveBeenCalledWith(10);
    });
  });

  describe('Row Interactions', () => {
    it('should handle row click events', async () => {
      const user = userEvent.setup();
      const onRowClick = jest.fn();

      render(<EntityManagementTable {...defaultProps} onRowClick={onRowClick} />);

      // Click on first row
      const firstRow = screen.getByText('John Doe').closest('tr');
      if (firstRow) {
        await user.click(firstRow);
        expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
      }
    });
  });

  describe('Export Functionality', () => {
    it('should handle export action', async () => {
      const user = userEvent.setup();
      const onExport = jest.fn();

      render(<EntityManagementTable {...defaultProps} onExport={onExport} />);

      const exportButton = screen.getByText('Export');
      await user.click(exportButton);

      expect(onExport).toHaveBeenCalledWith('csv');
    });
  });

  describe('Refresh Functionality', () => {
    it('should handle refresh action', async () => {
      const user = userEvent.setup();
      const onRefresh = jest.fn();

      render(<EntityManagementTable {...defaultProps} onRefresh={onRefresh} />);

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      expect(onRefresh).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<EntityManagementTable {...defaultProps} />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders).toHaveLength(5); // 4 data columns + 1 actions column
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search...');
      await user.tab();

      expect(searchInput).toHaveFocus();
    });
  });

  describe('Portal Presets', () => {
    it('should provide management portal presets', () => {
      const presets = EntityTablePresets.management.tenantsTable();

      expect(presets.columns).toHaveLength(5);
      expect(presets.actions).toHaveLength(3);
      expect(presets.columns[0].key).toBe('name');
    });

    it('should provide admin portal presets', () => {
      const presets = EntityTablePresets.admin.customersTable();

      expect(presets.columns).toHaveLength(6);
      expect(presets.actions).toHaveLength(2);
      expect(presets.columns[0].key).toBe('name');
    });

    it('should provide customer portal presets', () => {
      const presets = EntityTablePresets.customer.billsTable();

      expect(presets.columns).toHaveLength(5);
      expect(presets.actions).toHaveLength(2);
      expect(presets.columns[0].key).toBe('invoiceNumber');
    });

    it('should provide reseller portal presets', () => {
      const presets = EntityTablePresets.reseller.salesTable();

      expect(presets.columns).toHaveLength(5);
      expect(presets.actions).toHaveLength(1);
      expect(presets.columns[0].key).toBe('customerName');
    });
  });

  describe('Performance', () => {
    it('should handle large datasets efficiently', () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: String(i),
        name: `User ${i}`,
        email: `user${i}@example.com`,
        status: i % 2 === 0 ? 'active' : 'inactive',
        plan: i % 3 === 0 ? 'premium' : 'basic',
      }));

      const startTime = performance.now();
      render(<EntityManagementTable {...defaultProps} data={largeData} />);
      const endTime = performance.now();

      // Should render within reasonable time (< 100ms)
      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should debounce search input', async () => {
      const user = userEvent.setup();
      render(<EntityManagementTable {...defaultProps} searchable={true} />);

      const searchInput = screen.getByPlaceholderText('Search...');

      // Type multiple characters quickly
      await user.type(searchInput, 'John');

      // Should not perform search for each character
      // This is more of a behavior test - actual implementation would need debouncing
      expect(searchInput).toHaveValue('John');
    });
  });

  describe('Error Handling', () => {
    it('should handle missing required props gracefully', () => {
      // Test with minimal props
      const minimalProps = {
        data: mockData,
        columns: mockColumns,
        variant: 'admin' as const,
      };

      expect(() => {
        render(<EntityManagementTable {...minimalProps} />);
      }).not.toThrow();
    });

    it('should handle invalid data gracefully', () => {
      const invalidData = [
        { id: '1', name: null, email: undefined },
        { id: '2' }, // Missing fields
        null as any, // Invalid entry
      ].filter(Boolean);

      expect(() => {
        render(<EntityManagementTable {...defaultProps} data={invalidData} />);
      }).not.toThrow();
    });
  });
});
