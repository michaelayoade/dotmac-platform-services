'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Building2,
  Users,
  Shield,
  CreditCard,
  Settings,
  Plus,
  Edit,
  Trash2,
  MoreHorizontal,
  Mail,
  Phone,
  Globe,
  MapPin,
  Calendar,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Upload,
  Download,
  UserPlus,
  UserMinus,
  Crown,
  Key,
  Save,
  X,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  joinedAt: string;
  lastActive: string;
  avatar: string | null;
}

// Mock organization data
const mockOrganization = {
  id: 'org_123',
  name: 'Acme Corporation',
  slug: 'acme-corp',
  logo: null,
  description: 'Leading provider of innovative solutions',
  website: 'https://acme.example.com',
  email: 'contact@acme.example.com',
  phone: '+1 (555) 123-4567',
  address: {
    street: '123 Business Ave',
    city: 'San Francisco',
    state: 'CA',
    zip: '94105',
    country: 'United States',
  },
  industry: 'Technology',
  size: '50-200',
  founded: '2020',
  taxId: 'XX-XXXXXXX',
  plan: 'Enterprise',
  billingEmail: 'billing@acme.example.com',
  createdAt: '2020-01-15T10:00:00Z',
  updatedAt: '2024-01-20T15:30:00Z',
};

// Mock team members
const mockMembers = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@acme.example.com',
    role: 'Owner',
    status: 'active',
    joinedAt: '2020-01-15T10:00:00Z',
    lastActive: '2 hours ago',
    avatar: null,
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane@acme.example.com',
    role: 'Admin',
    status: 'active',
    joinedAt: '2020-02-01T10:00:00Z',
    lastActive: '5 minutes ago',
    avatar: null,
  },
  {
    id: '3',
    name: 'Bob Johnson',
    email: 'bob@acme.example.com',
    role: 'Member',
    status: 'active',
    joinedAt: '2020-03-15T10:00:00Z',
    lastActive: '1 day ago',
    avatar: null,
  },
  {
    id: '4',
    name: 'Alice Brown',
    email: 'alice@acme.example.com',
    role: 'Member',
    status: 'pending',
    joinedAt: '2024-01-20T10:00:00Z',
    lastActive: 'Never',
    avatar: null,
  },
];

// Mock departments
const mockDepartments = [
  { id: '1', name: 'Engineering', memberCount: 25, head: 'Jane Smith' },
  { id: '2', name: 'Sales', memberCount: 15, head: 'Bob Johnson' },
  { id: '3', name: 'Marketing', memberCount: 10, head: 'Alice Brown' },
  { id: '4', name: 'Support', memberCount: 8, head: 'John Doe' },
  { id: '5', name: 'HR', memberCount: 5, head: 'Sarah Wilson' },
];

export default function OrganizationSettingsPage() {
  const { toast } = useToast();

  const [organization, setOrganization] = useState(mockOrganization);
  const [members, setMembers] = useState(mockMembers);
  const [departments, setDepartments] = useState(mockDepartments);
  const [isEditing, setIsEditing] = useState(false);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [isAddDepartmentOpen, setIsAddDepartmentOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [isMemberEditOpen, setIsMemberEditOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Form states
  const [formData, setFormData] = useState(organization);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Member');
  const [newDepartment, setNewDepartment] = useState({ name: '', head: '' });

  const handleSaveOrganization = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setOrganization(formData);
      setIsEditing(false);
      setIsLoading(false);
      toast({ title: 'Success', description: 'Organization settings updated' });
    }, 1000);
  };

  const handleCancelEdit = () => {
    setFormData(organization);
    setIsEditing(false);
  };

  const handleInviteMember = () => {
    const newMember = {
      id: Date.now().toString(),
      name: inviteEmail.split('@')[0],
      email: inviteEmail,
      role: inviteRole,
      status: 'pending',
      joinedAt: new Date().toISOString(),
      lastActive: 'Never',
      avatar: null,
    };

    setMembers([...members, newMember]);
    setIsInviteOpen(false);
    setInviteEmail('');
    setInviteRole('Member');
    toast({ title: 'Success', description: `Invitation sent to ${inviteEmail}` });
  };

  const handleUpdateMemberRole = () => {
    if (!selectedMember) return;

    setMembers(members.map(member =>
      member.id === selectedMember.id
        ? { ...selectedMember }
        : member
    ));
    setIsMemberEditOpen(false);
    toast({ title: 'Success', description: 'Member role updated' });
  };

  const handleRemoveMember = (memberId: string) => {
    setMembers(members.filter(m => m.id !== memberId));
    toast({ title: 'Success', description: 'Member removed from organization' });
  };

  const handleAddDepartment = () => {
    const department = {
      id: Date.now().toString(),
      name: newDepartment.name,
      memberCount: 0,
      head: newDepartment.head,
    };

    setDepartments([...departments, department]);
    setIsAddDepartmentOpen(false);
    setNewDepartment({ name: '', head: '' });
    toast({ title: 'Success', description: 'Department added successfully' });
  };

  const handleDeleteDepartment = (deptId: string) => {
    setDepartments(departments.filter(d => d.id !== deptId));
    toast({ title: 'Success', description: 'Department deleted' });
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'Owner': return 'default';
      case 'Admin': return 'secondary';
      default: return 'outline';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'pending': return 'secondary';
      default: return 'outline';
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Organization Settings</h1>
        <p className="text-gray-500 mt-2">Manage your organization profile and team</p>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="members">Members</TabsTrigger>
          <TabsTrigger value="departments">Departments</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        {/* General Tab */}
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Organization Profile</CardTitle>
                  <CardDescription>Basic information about your organization</CardDescription>
                </div>
                {!isEditing ? (
                  <Button onClick={() => setIsEditing(true)}>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={handleCancelEdit}>
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button onClick={handleSaveOrganization} disabled={isLoading}>
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Logo Section */}
              <div className="flex items-center gap-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={organization.logo || undefined} />
                  <AvatarFallback>{organization.name.slice(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
                {isEditing && (
                  <div className="space-y-2">
                    <Button variant="outline" size="sm">
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Logo
                    </Button>
                    <p className="text-xs text-gray-500">PNG, JPG or SVG, max 2MB</p>
                  </div>
                )}
              </div>

              <Separator />

              {/* Organization Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="org-name">Organization Name</Label>
                  <Input
                    id="org-name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-slug">URL Slug</Label>
                  <Input
                    id="org-slug"
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    disabled={!isEditing}
                    placeholder="acme-corp"
                  />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="org-description">Description</Label>
                  <Textarea
                    id="org-description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    disabled={!isEditing}
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-website">Website</Label>
                  <Input
                    id="org-website"
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-email">Contact Email</Label>
                  <Input
                    id="org-email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-phone">Phone Number</Label>
                  <Input
                    id="org-phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-industry">Industry</Label>
                  <select
                    id="org-industry"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    disabled={!isEditing}
                    className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
                  >
                    <option value="Technology">Technology</option>
                    <option value="Finance">Finance</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="Education">Education</option>
                    <option value="Retail">Retail</option>
                    <option value="Manufacturing">Manufacturing</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-size">Company Size</Label>
                  <select
                    id="org-size"
                    value={formData.size}
                    onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                    disabled={!isEditing}
                    className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
                  >
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="50-200">50-200 employees</option>
                    <option value="200-500">200-500 employees</option>
                    <option value="500+">500+ employees</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-founded">Founded Year</Label>
                  <Input
                    id="org-founded"
                    value={formData.founded}
                    onChange={(e) => setFormData({ ...formData, founded: e.target.value })}
                    disabled={!isEditing}
                    placeholder="2020"
                  />
                </div>
              </div>

              {/* Address Section */}
              <div className="space-y-4">
                <h3 className="font-semibold">Address</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="org-street">Street Address</Label>
                    <Input
                      id="org-street"
                      value={formData.address.street}
                      onChange={(e) => setFormData({
                        ...formData,
                        address: { ...formData.address, street: e.target.value }
                      })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-city">City</Label>
                    <Input
                      id="org-city"
                      value={formData.address.city}
                      onChange={(e) => setFormData({
                        ...formData,
                        address: { ...formData.address, city: e.target.value }
                      })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-state">State/Province</Label>
                    <Input
                      id="org-state"
                      value={formData.address.state}
                      onChange={(e) => setFormData({
                        ...formData,
                        address: { ...formData.address, state: e.target.value }
                      })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-zip">ZIP/Postal Code</Label>
                    <Input
                      id="org-zip"
                      value={formData.address.zip}
                      onChange={(e) => setFormData({
                        ...formData,
                        address: { ...formData.address, zip: e.target.value }
                      })}
                      disabled={!isEditing}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-country">Country</Label>
                    <Input
                      id="org-country"
                      value={formData.address.country}
                      onChange={(e) => setFormData({
                        ...formData,
                        address: { ...formData.address, country: e.target.value }
                      })}
                      disabled={!isEditing}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Members Tab */}
        <TabsContent value="members" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Team Members</CardTitle>
                  <CardDescription>Manage your organization\'s team members</CardDescription>
                </div>
                <Button onClick={() => setIsInviteOpen(true)}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Invite Member
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Member</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead>Last Active</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member) => (
                    <TableRow key={member.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-8 w-8">
                            <AvatarImage src={member.avatar || undefined} />
                            <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{member.name}</div>
                            <div className="text-sm text-gray-500">{member.email}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getRoleBadgeVariant(member.role)}>
                          {member.role === 'Owner' && <Crown className="h-3 w-3 mr-1" />}
                          {member.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(member.status)}>
                          {member.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(member.joinedAt).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{member.lastActive}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => {
                                if (member.role !== 'Owner') {
                                  setSelectedMember(member);
                                  setIsMemberEditOpen(true);
                                }
                              }}
                              className={member.role === 'Owner' ? 'opacity-50 cursor-not-allowed' : ''}
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Edit Role
                            </DropdownMenuItem>
                            {member.status === 'pending' && (
                              <DropdownMenuItem>
                                <Mail className="h-4 w-4 mr-2" />
                                Resend Invite
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => {
                                if (member.role !== 'Owner') {
                                  handleRemoveMember(member.id);
                                }
                              }}
                              className={`text-red-600 ${member.role === 'Owner' ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                              <UserMinus className="h-4 w-4 mr-2" />
                              Remove
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Team Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Members</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{members.length}</div>
                <p className="text-xs text-muted-foreground">
                  {members.filter(m => m.status === 'active').length} active
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending Invites</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {members.filter(m => m.status === 'pending').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  Awaiting acceptance
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Admins</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {members.filter(m => m.role === 'Admin' || m.role === 'Owner').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  With admin privileges
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Departments Tab */}
        <TabsContent value="departments" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Departments</CardTitle>
                  <CardDescription>Organize your team into departments</CardDescription>
                </div>
                <Button onClick={() => setIsAddDepartmentOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Department
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Department</TableHead>
                    <TableHead>Head</TableHead>
                    <TableHead>Members</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {departments.map((dept) => (
                    <TableRow key={dept.id}>
                      <TableCell className="font-medium">{dept.name}</TableCell>
                      <TableCell>{dept.head}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{dept.memberCount} members</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Users className="h-4 w-4 mr-2" />
                              Manage Members
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDeleteDepartment(dept.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Billing Information</CardTitle>
              <CardDescription>Manage your organization\'s billing details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">Current Plan</p>
                  <p className="text-sm text-gray-500">You are on the {organization.plan} plan</p>
                </div>
                <Badge variant="default" className="text-lg px-3 py-1">
                  {organization.plan}
                </Badge>
              </div>
              <Separator />
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="billing-email">Billing Email</Label>
                    <Input
                      id="billing-email"
                      type="email"
                      value={organization.billingEmail}
                      disabled
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tax-id">Tax ID</Label>
                    <Input
                      id="tax-id"
                      value={organization.taxId}
                      disabled
                    />
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <CreditCard className="h-4 w-4 mr-2" />
                  Update Payment Method
                </Button>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download Invoices
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>Configure organization-wide security settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Require 2FA for all members</Label>
                  <p className="text-sm text-gray-500">Enforce two-factor authentication</p>
                </div>
                <Switch />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>IP allowlist</Label>
                  <p className="text-sm text-gray-500">Restrict access to specific IP addresses</p>
                </div>
                <Switch />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Session timeout</Label>
                  <p className="text-sm text-gray-500">Automatically log out inactive users</p>
                </div>
                <select
                  defaultValue="30"
                  className="h-10 w-[150px] rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
                >
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="60">1 hour</option>
                  <option value="240">4 hours</option>
                  <option value="never">Never</option>
                </select>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>SSO (Single Sign-On)</Label>
                  <p className="text-sm text-gray-500">Enable SSO with your identity provider</p>
                </div>
                <Button variant="outline" size="sm">
                  Configure
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage API keys for programmatic access</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">No API keys created yet</p>
                <Button variant="outline">
                  <Key className="h-4 w-4 mr-2" />
                  Create API Key
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Invite Member Dialog */}
      <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Team Member</DialogTitle>
            <DialogDescription>
              Send an invitation to join your organization
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email Address</Label>
              <Input
                id="invite-email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
              >
                <option value="Member">Member</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsInviteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleInviteMember} disabled={!inviteEmail}>
              Send Invitation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Member Dialog */}
      <Dialog open={isMemberEditOpen} onOpenChange={setIsMemberEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Member Role</DialogTitle>
            <DialogDescription>
              Update the role for {selectedMember?.name}
            </DialogDescription>
          </DialogHeader>
          {selectedMember && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-role">Role</Label>
                <select
                  id="edit-role"
                  value={selectedMember.role}
                  onChange={(e) => setSelectedMember({ ...selectedMember, role: e.target.value })}
                  className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
                >
                  <option value="Member">Member</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsMemberEditOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateMemberRole}>
              Update Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Department Dialog */}
      <Dialog open={isAddDepartmentOpen} onOpenChange={setIsAddDepartmentOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Department</DialogTitle>
            <DialogDescription>
              Create a new department in your organization
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="dept-name">Department Name</Label>
              <Input
                id="dept-name"
                value={newDepartment.name}
                onChange={(e) => setNewDepartment({ ...newDepartment, name: e.target.value })}
                placeholder="e.g., Engineering"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dept-head">Department Head</Label>
              <select
                id="dept-head"
                value={newDepartment.head}
                onChange={(e) => setNewDepartment({ ...newDepartment, head: e.target.value })}
                className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"
              >
                <option value="">Select head</option>
                {members.filter(m => m.status === 'active').map(member => (
                  <option key={member.id} value={member.name}>
                    {member.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDepartmentOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddDepartment} disabled={!newDepartment.name || !newDepartment.head}>
              Add Department
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}