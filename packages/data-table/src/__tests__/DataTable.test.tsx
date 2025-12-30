import { render, screen, fireEvent, within } from "@testing-library/react";
import { DataTable, type ColumnDef } from "../DataTable";

interface TestData {
  id: string;
  name: string;
  email: string;
  status: "active" | "inactive";
}

const testData: TestData[] = [
  { id: "1", name: "John Doe", email: "john@example.com", status: "active" },
  { id: "2", name: "Jane Smith", email: "jane@example.com", status: "inactive" },
  { id: "3", name: "Bob Wilson", email: "bob@example.com", status: "active" },
];

const columns: ColumnDef<TestData, unknown>[] = [
  { id: "name", accessorKey: "name", header: "Name" },
  { id: "email", accessorKey: "email", header: "Email" },
  { id: "status", accessorKey: "status", header: "Status" },
];

describe("DataTable", () => {
  it("should render table with data", () => {
    render(<DataTable data={testData} columns={columns} />);

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
    // Multiple rows have "active" status
    expect(screen.getAllByText("active").length).toBeGreaterThan(0);
  });

  it("should render column headers", () => {
    render(<DataTable data={testData} columns={columns} />);

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("should show empty state when no data", () => {
    render(<DataTable data={[]} columns={columns} />);

    expect(screen.getByText("No results.")).toBeInTheDocument();
  });

  it("should show loading state", () => {
    render(<DataTable data={[]} columns={columns} loading />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("should show error message", () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        error="Failed to load data"
      />
    );

    expect(screen.getByText("Failed to load data")).toBeInTheDocument();
  });

  it("should filter data with search", () => {
    render(<DataTable data={testData} columns={columns} searchable />);

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "jane" } });

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
  });

  it("should handle row selection", () => {
    const onSelectionChange = jest.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        selectable
        onSelectionChange={onSelectionChange}
      />
    );

    // Find the first row checkbox (not header)
    const checkboxes = screen.getAllByRole("checkbox");
    const rowCheckbox = checkboxes[1]; // Skip header checkbox

    fireEvent.click(rowCheckbox);

    expect(onSelectionChange).toHaveBeenCalled();
  });

  it("should toggle column visibility", () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        columnVisibility
      />
    );

    // Click the Columns button
    const columnsButton = screen.getByText("Columns");
    fireEvent.click(columnsButton);

    // Find and uncheck the Email column
    const emailCheckbox = screen.getByRole("checkbox", { name: /email/i });
    fireEvent.click(emailCheckbox);

    // Email column should be hidden
    expect(screen.queryByText("jane@example.com")).not.toBeInTheDocument();
  });

  it("should sort columns when clicked", () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        sortable
      />
    );

    // Click on Name header to sort
    const nameHeader = screen.getByText("Name");
    fireEvent.click(nameHeader);

    // After sorting, Bob should appear before Jane and John
    const rows = screen.getAllByRole("row");
    const firstDataRow = rows[1]; // Skip header row

    expect(within(firstDataRow).getByText("Bob Wilson")).toBeInTheDocument();
  });

  it("should render pagination controls", () => {
    const moreData = Array.from({ length: 25 }, (_, i) => ({
      id: String(i),
      name: `User ${i}`,
      email: `user${i}@example.com`,
      status: "active" as const,
    }));

    render(
      <DataTable
        data={moreData}
        columns={columns}
        pagination
        defaultPageSize={10}
      />
    );

    expect(screen.getByText("Previous")).toBeInTheDocument();
    expect(screen.getByText("Next")).toBeInTheDocument();
  });

  it("should navigate pages", () => {
    const moreData = Array.from({ length: 25 }, (_, i) => ({
      id: String(i),
      name: `User ${i}`,
      email: `user${i}@example.com`,
      status: "active" as const,
    }));

    render(
      <DataTable
        data={moreData}
        columns={columns}
        pagination
        defaultPageSize={10}
      />
    );

    // First page should show User 0
    expect(screen.getByText("User 0")).toBeInTheDocument();

    // Click next
    const nextButton = screen.getByText("Next");
    fireEvent.click(nextButton);

    // Should now show User 10
    expect(screen.getByText("User 10")).toBeInTheDocument();
    expect(screen.queryByText("User 0")).not.toBeInTheDocument();
  });

  it("should handle bulk actions", async () => {
    const handleDelete = jest.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        selectable
        bulkActions={[
          {
            label: "Delete",
            action: handleDelete,
            variant: "destructive",
          },
        ]}
      />
    );

    // Select first row
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);

    // Click delete button
    const deleteButton = screen.getByText("Delete");
    fireEvent.click(deleteButton);

    expect(handleDelete).toHaveBeenCalledWith([testData[0]]);
  });

  it("should hide toolbar when hideToolbar is true", () => {
    render(
      <DataTable
        data={testData}
        columns={columns}
        searchable
        hideToolbar
      />
    );

    expect(screen.queryByPlaceholderText("Search...")).not.toBeInTheDocument();
  });

  it("should call onRowClick when row is clicked", () => {
    const onRowClick = jest.fn();

    render(
      <DataTable
        data={testData}
        columns={columns}
        onRowClick={onRowClick}
      />
    );

    const firstRow = screen.getByText("John Doe").closest("tr");
    if (firstRow) {
      fireEvent.click(firstRow);
    }

    expect(onRowClick).toHaveBeenCalledWith(testData[0]);
  });
});
