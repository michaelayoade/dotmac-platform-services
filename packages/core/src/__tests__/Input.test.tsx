import { render, screen, fireEvent } from "@testing-library/react";
import { Input, InputGroup } from "../primitives/Input";

describe("Input", () => {
  it("should render an input element", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("should apply size classes", () => {
    render(<Input size="lg" placeholder="Large input" />);
    const input = screen.getByPlaceholderText("Large input");
    expect(input).toHaveClass("h-12");
  });

  it("should apply variant classes", () => {
    render(<Input variant="filled" placeholder="Filled input" />);
    const input = screen.getByPlaceholderText("Filled input");
    expect(input).toHaveClass("bg-muted/50");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<Input disabled placeholder="Disabled" />);
    expect(screen.getByPlaceholderText("Disabled")).toBeDisabled();
  });

  it("should show error state", () => {
    render(<Input error="This field is required" id="test-input" />);
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("should display error message", () => {
    render(<Input error="This field is required" id="test-input" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("should display helper text", () => {
    render(<Input helperText="Enter your email" id="test-input" />);
    expect(screen.getByText("Enter your email")).toBeInTheDocument();
  });

  it("should show error message over helper text when both provided", () => {
    render(
      <Input
        error="Invalid email"
        helperText="Enter your email"
        id="test-input"
      />
    );
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
    expect(screen.queryByText("Enter your email")).not.toBeInTheDocument();
  });

  it("should handle value changes", () => {
    const handleChange = jest.fn();
    render(<Input onChange={handleChange} placeholder="Type here" />);

    const input = screen.getByPlaceholderText("Type here");
    fireEvent.change(input, { target: { value: "test" } });

    expect(handleChange).toHaveBeenCalled();
  });

  it("should render left addon", () => {
    render(
      <Input
        leftAddon={<span data-testid="left-addon">$</span>}
        placeholder="Amount"
      />
    );
    expect(screen.getByTestId("left-addon")).toBeInTheDocument();
  });

  it("should render right addon", () => {
    render(
      <Input
        rightAddon={<span data-testid="right-addon">.00</span>}
        placeholder="Amount"
      />
    );
    expect(screen.getByTestId("right-addon")).toBeInTheDocument();
  });

  it("should apply left padding when leftAddon is present", () => {
    render(
      <Input
        leftAddon={<span>$</span>}
        placeholder="Amount"
      />
    );
    const input = screen.getByPlaceholderText("Amount");
    expect(input).toHaveClass("pl-10");
  });

  it("should apply right padding when rightAddon is present", () => {
    render(
      <Input
        rightAddon={<span>.00</span>}
        placeholder="Amount"
      />
    );
    const input = screen.getByPlaceholderText("Amount");
    expect(input).toHaveClass("pr-10");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<Input ref={ref} placeholder="Ref input" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("should apply custom className", () => {
    render(<Input className="custom-class" placeholder="Custom" />);
    const input = screen.getByPlaceholderText("Custom");
    expect(input).toHaveClass("custom-class");
  });

  it("should apply container className", () => {
    const { container } = render(
      <Input containerClassName="container-class" placeholder="Container" />
    );
    expect(container.firstChild).toHaveClass("container-class");
  });

  it("should render different input types", () => {
    render(<Input type="email" placeholder="Email" />);
    const input = screen.getByPlaceholderText("Email");
    expect(input).toHaveAttribute("type", "email");
  });

  it("should set aria-describedby for error message", () => {
    render(<Input error="Error" id="my-input" />);
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-describedby", "my-input-error");
  });

  it("should set aria-describedby for helper text", () => {
    render(<Input helperText="Helper" id="my-input" />);
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-describedby", "my-input-helper");
  });
});

describe("InputGroup", () => {
  it("should render children", () => {
    render(
      <InputGroup>
        <Input placeholder="Input 1" />
        <Input placeholder="Input 2" />
      </InputGroup>
    );

    expect(screen.getByPlaceholderText("Input 1")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Input 2")).toBeInTheDocument();
  });

  it("should apply flex display", () => {
    const { container } = render(
      <InputGroup>
        <Input placeholder="Input" />
      </InputGroup>
    );

    expect(container.firstChild).toHaveClass("flex");
  });

  it("should apply custom className", () => {
    const { container } = render(
      <InputGroup className="custom-group">
        <Input placeholder="Input" />
      </InputGroup>
    );

    expect(container.firstChild).toHaveClass("custom-group");
  });
});
