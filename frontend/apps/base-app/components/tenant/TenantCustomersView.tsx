'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, AlertCircle } from 'lucide-react';
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

export default function TenantCustomersView() {
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
    deleteCustomer,
  } = useCustomers();

  useEffect(() => {
    const searchParams: {
      query?: string;
      status?: string;
      tier?: string;
    } = {
      query: searchQuery || undefined,
      status: selectedStatus !== 'all' ? selectedStatus : undefined,
      tier: selectedTier !== 'all' ? selectedTier : undefined,
    };

    Object.keys(searchParams).forEach(
      (key) =>
        searchParams[key as keyof typeof searchParams] === undefined &&
        delete searchParams[key as keyof typeof searchParams],
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
      toast.success(
        `Customer "${customerToDelete.display_name || customerToDelete.email}" deleted successfully`,
      );
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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Customer Management</h1>
          <p className="text-sm text-muted-foreground">
            Track relationships, segment accounts, and take action on high-impact customers.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button onClick={handleCreateCustomer}>
            <Plus className="h-4 w-4 mr-2" />
            Create Customer
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

       <CustomersMetrics metrics={metrics} loading={loading} />

      <div className="grid gap-4 md:grid-cols-3">
        <div className="relative">
          <span className="sr-only" id="customers-search-label">
            Search customers
          </span>
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden />
          <input
            type="search"
            aria-labelledby="customers-search-label"
            placeholder="Search customers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" aria-hidden />
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full rounded-md border border-border bg-background py-2 px-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="trialing">Trialing</option>
            <option value="past_due">Past Due</option>
            <option value="churned">Churned</option>
          </select>
        </div>
        <div>
          <select
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
            className="w-full rounded-md border border-border bg-background py-2 px-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="all">All plans</option>
            <option value="starter">Starter</option>
            <option value="professional">Professional</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>

      <CustomersList
        customers={customers}
        loading={loading}
        onCustomerSelect={handleViewCustomer}
        onEditCustomer={handleEditCustomer}
        onDeleteCustomer={handleDeleteCustomer}
      />

      {showCreateModal && (
        <CreateCustomerModal
          onClose={() => setShowCreateModal(false)}
          onCustomerCreated={handleCustomerCreated}
          createCustomer={createCustomer}
          updateCustomer={updateCustomer}
        />
      )}

      {showEditModal && selectedCustomer && (
        <CustomerEditModal
          customer={selectedCustomer}
          onClose={() => setShowEditModal(false)}
          onCustomerUpdated={handleCustomerUpdated}
          updateCustomer={updateCustomer}
        />
      )}

      {showViewModal && selectedCustomer && (
        <CustomerViewModal
          customer={selectedCustomer}
          onClose={() => setShowViewModal(false)}
        />
      )}

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete customer</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{' '}
              <span className="font-semibold">
                {customerToDelete?.display_name || customerToDelete?.email}
              </span>
              ? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4" aria-hidden />
            <p>
              Removing a customer deletes their profile, notes, and tracked metrics. Historical revenue is preserved.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDeleteCustomer} disabled={isDeleting}>
              {isDeleting ? 'Deleting...' : 'Delete customer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
