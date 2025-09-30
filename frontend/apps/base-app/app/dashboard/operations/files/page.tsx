'use client';

import React from 'react';

export default function FilesPage() {
  return (
    <div className="container mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">File Operations</h1>
          <p className="text-gray-600">File management functionality is currently being developed.</p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            This page is temporarily disabled while we migrate the UI components.
            The file operations API endpoints are fully functional and can be accessed programmatically.
          </p>
        </div>
      </div>
    </div>
  );
}