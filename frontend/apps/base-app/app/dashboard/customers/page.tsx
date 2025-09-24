'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, MoreHorizontal } from 'lucide-react';
import { CustomersList } from '@/components/customers/CustomersList';
import { CustomersMetrics } from '@/components/customers/CustomersMetrics';
import { CreateCustomerModal } from '@/components/customers/CreateCustomerModal';
import { useCustomers } from '@/hooks/useCustomers';

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedTier, setSelectedTier] = useState('all');

  const {
    customers,
    loading,
    metrics,
    searchCustomers,
    refreshCustomers
  } = useCustomers();

  useEffect(() => {
    // Trigger search when filters change
    const searchParams = {
      query: searchQuery || undefined,
      status: selectedStatus !== 'all' ? selectedStatus : undefined,
      tier: selectedTier !== 'all' ? selectedTier : undefined,
    };
    searchCustomers(searchParams);
  }, [searchQuery, selectedStatus, selectedTier, searchCustomers]);

  const handleCreateCustomer = () => {
    setShowCreateModal(true);
  };

  const handleCustomerCreated = () => {
    setShowCreateModal(false);
    refreshCustomers();
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Customer Management</h1>
          <p className="text-slate-400">Manage customer relationships and track interactions</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleCreateCustomer}
            className="flex items-center gap-2 bg-sky-500 hover:bg-sky-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
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
      <div className="bg-slate-900 rounded-lg p-6 mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search customers by name, email, or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="lg:w-48">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
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
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
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
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Customers List */}
      <div className="bg-slate-900 rounded-lg overflow-hidden">
        <CustomersList
          customers={customers}
          loading={loading}
          onCustomerSelect={(customer) => {
            // Handle customer selection - could open detail modal or navigate
            console.log('Selected customer:', customer);
          }}
        />
      </div>

      {/* Create Customer Modal */}
      {showCreateModal && (
        <CreateCustomerModal
          onClose={() => setShowCreateModal(false)}
          onCustomerCreated={handleCustomerCreated}
        />
      )}
    </div>
  );
}