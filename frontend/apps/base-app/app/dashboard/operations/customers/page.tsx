'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, MoreHorizontal, AlertCircle } from 'lucide-react';
import { CustomersList } from '@/components/customers/CustomersList';
import { CustomersMetrics } from '@/components/customers/CustomersMetrics';
import { CreateCustomerModal } from '@/components/customers/CreateCustomerModal';
import { CustomerViewModal } from '@/components/customers/CustomerViewModal';
import { CustomerEditModal } from '@/components/customers/CustomerEditModal';
import { useCustomers } from '@/hooks/useCustomers';
import { Customer } from '@/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerToDelete, setCustomerToDelete] = useState<Customer | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedTier, setSelectedTier] = useState('all');

  const {
    customers,
    loading,
    metrics,
    searchCustomers,
    refreshCustomers,
    createCustomer,
    updateCustomer,
    deleteCustomer
  } = useCustomers();

  useEffect(() => {
    // Trigger search when filters change
    const searchParams: {
      query?: string;
      status?: string;
      tier?: string;
    } = {
      query: searchQuery || undefined,
      status: selectedStatus !== 'all' ? selectedStatus : undefined,
      tier: selectedTier !== 'all' ? selectedTier : undefined,
    };
    // Remove undefined values
    Object.keys(searchParams).forEach(key =>
      searchParams[key as keyof typeof searchParams] === undefined &&
      delete searchParams[key as keyof typeof searchParams]
    );
    searchCustomers(searchParams as any);
  }, [searchQuery, selectedStatus, selectedTier, searchCustomers]);

  const handleCreateCustomer = () => {
    setShowCreateModal(true);
  };

  const handleCustomerCreated = () => {
    setShowCreateModal(false);
    refreshCustomers();
  };

  const handleEditCustomer = (customer: Customer) => {
    setSelectedCustomer(customer);
    setShowEditModal(true);
  };

  const handleViewCustomer = (customer: Customer) => {
    setSelectedCustomer(customer);
    setShowViewModal(true);
  };

  const handleDeleteCustomer = (customer: Customer) => {
    setCustomerToDelete(customer);
    setShowDeleteDialog(true);
  };

  const confirmDeleteCustomer = async () => {
    if (!customerToDelete || !deleteCustomer) return;

    setIsDeleting(true);
    try {
      await deleteCustomer(customerToDelete.id);
      refreshCustomers();
      setShowDeleteDialog(false);
      setCustomerToDelete(null);
      toast.success(`Customer "${customerToDelete.display_name || customerToDelete.email}" deleted successfully`);
    } catch (error) {
      console.error('Failed to delete customer:', error);
      toast.error('Failed to delete customer. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setShowDeleteDialog(false);
    setCustomerToDelete(null);
  };

  const handleCustomerUpdated = () => {
    setShowEditModal(false);
    setSelectedCustomer(null);
    refreshCustomers();
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Customer Management</h1>
          <p className="text-muted-foreground">Manage customer relationships and track interactions</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleCreateCustomer}
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Customer
          </button>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="mb-8">
        <CustomersMetrics metrics={metrics} loading={loading} />
      </div>

      {/* Search and Filters */}
      <div className="bg-card rounded-lg p-6 mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <input
                type="text"
                placeholder="Search customers by name, email, or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="lg:w-48">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              aria-label="Filter by customer status"
              className="w-full px-3 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="prospect">Prospect</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="churned">Churned</option>
            </select>
          </div>

          {/* Tier Filter */}
          <div className="lg:w-48">
            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              aria-label="Filter by customer tier"
              className="w-full px-3 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            >
              <option value="all">All Tiers</option>
              <option value="free">Free</option>
              <option value="basic">Basic</option>
              <option value="standard">Standard</option>
              <option value="premium">Premium</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {/* Export Button */}
          <button
            type="button"
            className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-input rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Customers List */}
      <div className="bg-card rounded-lg overflow-hidden">
        <CustomersList
          customers={customers}
          loading={loading}
          onCustomerSelect={handleViewCustomer}
          onEditCustomer={handleEditCustomer}
          onDeleteCustomer={handleDeleteCustomer}
        />
      </div>

      {/* Create Customer Modal */}
      {showCreateModal && (
        <CreateCustomerModal
          onClose={() => setShowCreateModal(false)}
          onCustomerCreated={handleCustomerCreated}
          createCustomer={createCustomer}
          updateCustomer={updateCustomer}
          loading={loading}
        />
      )}

      {/* View Customer Modal */}
      {showViewModal && selectedCustomer && (
        <CustomerViewModal
          customer={selectedCustomer}
          onClose={() => {
            setShowViewModal(false);
            setSelectedCustomer(null);
          }}
        />
      )}

      {/* Edit Customer Modal */}
      {showEditModal && selectedCustomer && (
        <CustomerEditModal
          customer={selectedCustomer}
          onClose={() => {
            setShowEditModal(false);
            setSelectedCustomer(null);
          }}
          onCustomerUpdated={handleCustomerUpdated}
          updateCustomer={updateCustomer}
          loading={loading}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Customer</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this customer? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {customerToDelete && (
            <div className="py-4">
              <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-md p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-red-800 dark:text-red-300">
                      You are about to delete <strong>{customerToDelete.display_name || customerToDelete.email}</strong>
                    </p>
                    <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                      All data associated with this customer will be permanently removed.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete} disabled={isDeleting}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteCustomer}
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete Customer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}