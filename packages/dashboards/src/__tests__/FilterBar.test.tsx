import { render, screen, fireEvent } from "@testing-library/react";
import { FilterBar, type FilterConfig } from "../components/FilterBar";

describe("FilterBar", () => {
  const filters: FilterConfig[] = [
    {
      id: "status",
      label: "Status",
      type: "select",
      options: [
        { value: "active", label: "Active" },
        { value: "inactive", label: "Inactive" },
      ],
    },
    {
      id: "date",
      label: "Date",
      type: "date",
    },
    {
      id: "tags",
      label: "Tags",
      type: "multiselect",
      options: [
        { value: "urgent", label: "Urgent" },
        { value: "important", label: "Important" },
        { value: "low", label: "Low Priority" },
      ],
    },
    {
      id: "dateRange",
      label: "Date Range",
      type: "daterange",
    },
  ];

  it("should render search input by default", () => {
    render(<FilterBar filters={[]} />);

    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();
  });

  it("should hide search when showSearch is false", () => {
    render(<FilterBar filters={[]} showSearch={false} />);

    expect(screen.queryByPlaceholderText("Search...")).not.toBeInTheDocument();
  });

  it("should render select filter", () => {
    render(<FilterBar filters={[filters[0]]} />);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("should call onChange when select value changes", () => {
    const onChange = jest.fn();

    render(<FilterBar filters={[filters[0]]} onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "active" } });

    expect(onChange).toHaveBeenCalledWith({ status: "active" });
  });

  it("should render date filter", () => {
    render(<FilterBar filters={[filters[1]]} showSearch={false} />);

    // Date inputs are rendered as input[type="date"]
    const dateInput = document.querySelector('input[type="date"]');
    expect(dateInput).toBeInTheDocument();
  });

  it("should call onChange when date changes", () => {
    const onChange = jest.fn();

    render(<FilterBar filters={[filters[1]]} showSearch={false} onChange={onChange} />);

    const dateInput = document.querySelector('input[type="date"]') as HTMLInputElement;
    fireEvent.change(dateInput, { target: { value: "2024-01-15" } });

    expect(onChange).toHaveBeenCalledWith({ date: "2024-01-15" });
  });

  it("should render multiselect filter", () => {
    render(<FilterBar filters={[filters[2]]} />);

    // Should have a button to open the multiselect
    expect(screen.getByRole("button", { name: /tags/i })).toBeInTheDocument();
  });

  it("should open multiselect dropdown on click", () => {
    render(<FilterBar filters={[filters[2]]} />);

    const button = screen.getByRole("button", { name: /tags/i });
    fireEvent.click(button);

    expect(screen.getByText("Urgent")).toBeInTheDocument();
    expect(screen.getByText("Important")).toBeInTheDocument();
    expect(screen.getByText("Low Priority")).toBeInTheDocument();
  });

  it("should select items in multiselect", () => {
    const onChange = jest.fn();

    render(<FilterBar filters={[filters[2]]} onChange={onChange} />);

    const button = screen.getByRole("button", { name: /tags/i });
    fireEvent.click(button);

    fireEvent.click(screen.getByText("Urgent"));
    expect(onChange).toHaveBeenCalledWith({ tags: ["urgent"] });
  });

  it("should select multiple items in multiselect with existing values", () => {
    const onChange = jest.fn();

    render(
      <FilterBar
        filters={[filters[2]]}
        values={{ tags: ["urgent"] }}
        onChange={onChange}
      />
    );

    const button = screen.getByRole("button", { name: /urgent/i });
    fireEvent.click(button);

    fireEvent.click(screen.getByText("Important"));
    expect(onChange).toHaveBeenCalledWith({ tags: ["urgent", "important"] });
  });

  it("should show selected count in multiselect", () => {
    render(
      <FilterBar
        filters={[filters[2]]}
        values={{ tags: ["urgent", "important"] }}
      />
    );

    expect(screen.getByText("2 selected")).toBeInTheDocument();
  });

  it("should render daterange filter with two inputs", () => {
    render(<FilterBar filters={[filters[3]]} showSearch={false} />);

    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs).toHaveLength(2);
    expect(screen.getByText("to")).toBeInTheDocument();
  });

  it("should call onChange with array for daterange start", () => {
    const onChange = jest.fn();

    render(<FilterBar filters={[filters[3]]} showSearch={false} onChange={onChange} />);

    const dateInputs = document.querySelectorAll('input[type="date"]');

    fireEvent.change(dateInputs[0], { target: { value: "2024-01-01" } });
    expect(onChange).toHaveBeenCalledWith({ dateRange: ["2024-01-01", ""] });
  });

  it("should call onChange with array for daterange end", () => {
    const onChange = jest.fn();

    render(<FilterBar filters={[filters[3]]} showSearch={false} onChange={onChange} />);

    const dateInputs = document.querySelectorAll('input[type="date"]');

    fireEvent.change(dateInputs[1], { target: { value: "2024-01-31" } });
    expect(onChange).toHaveBeenCalledWith({ dateRange: ["", "2024-01-31"] });
  });

  it("should show More Filters button when more than 3 filters", () => {
    render(<FilterBar filters={filters} />);

    expect(screen.getByText("More Filters")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Badge showing count
  });

  it("should expand additional filters on More Filters click", () => {
    render(<FilterBar filters={filters} />);

    const moreButton = screen.getByText("More Filters");
    fireEvent.click(moreButton);

    // The 4th filter (daterange) should now be visible - it has 2 date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBeGreaterThan(1);
  });

  it("should show Clear all button when filters have values", () => {
    render(
      <FilterBar
        filters={filters}
        values={{ status: "active" }}
      />
    );

    expect(screen.getByText("Clear all")).toBeInTheDocument();
  });

  it("should clear all filters on Clear all click", () => {
    const onChange = jest.fn();
    const onSearchChange = jest.fn();

    render(
      <FilterBar
        filters={filters}
        values={{ status: "active" }}
        searchValue="test"
        onChange={onChange}
        onSearchChange={onSearchChange}
      />
    );

    fireEvent.click(screen.getByText("Clear all"));

    expect(onChange).toHaveBeenCalledWith({
      status: undefined,
      date: undefined,
      tags: undefined,
      dateRange: undefined,
    });
    expect(onSearchChange).toHaveBeenCalledWith("");
  });

  it("should render custom actions", () => {
    render(
      <FilterBar
        filters={[]}
        actions={<button>Custom Action</button>}
      />
    );

    expect(screen.getByText("Custom Action")).toBeInTheDocument();
  });

  it("should call onSearchChange when search input changes", () => {
    const onSearchChange = jest.fn();

    render(<FilterBar filters={[]} onSearchChange={onSearchChange} />);

    const searchInput = screen.getByPlaceholderText("Search...");
    fireEvent.change(searchInput, { target: { value: "test query" } });

    expect(onSearchChange).toHaveBeenCalledWith("test query");
  });
});
