import { render, screen, fireEvent } from "@testing-library/react";
import { Button, ButtonGroup } from "../primitives/Button";

describe("Button", () => {
  it("should render with children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("should apply variant classes", () => {
    render(<Button variant="primary">Primary</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("inline-flex");
  });

  it("should apply size classes", () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("h-11");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("should be disabled when loading", () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("should show loading spinner when loading", () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button.querySelector("svg")).toBeInTheDocument();
  });

  it("should handle click events", () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("should not trigger click when disabled", () => {
    const handleClick = jest.fn();
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    );

    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("should render left icon", () => {
    render(
      <Button leftIcon={<span data-testid="left-icon">←</span>}>
        With Icon
      </Button>
    );
    expect(screen.getByTestId("left-icon")).toBeInTheDocument();
  });

  it("should render right icon", () => {
    render(
      <Button rightIcon={<span data-testid="right-icon">→</span>}>
        With Icon
      </Button>
    );
    expect(screen.getByTestId("right-icon")).toBeInTheDocument();
  });

  it("should apply fullWidth class when fullWidth is true", () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByRole("button")).toHaveClass("w-full");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<Button ref={ref}>Ref Button</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("should apply custom className", () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByRole("button")).toHaveClass("custom-class");
  });

  it("should render as child when asChild is true", () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    );
    expect(screen.getByRole("link", { name: /link button/i })).toBeInTheDocument();
  });
});

describe("ButtonGroup", () => {
  it("should render children", () => {
    render(
      <ButtonGroup>
        <Button>One</Button>
        <Button>Two</Button>
      </ButtonGroup>
    );

    expect(screen.getByRole("button", { name: /one/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /two/i })).toBeInTheDocument();
  });

  it("should have group role", () => {
    render(
      <ButtonGroup>
        <Button>One</Button>
        <Button>Two</Button>
      </ButtonGroup>
    );

    expect(screen.getByRole("group")).toBeInTheDocument();
  });

  it("should apply horizontal orientation by default", () => {
    render(
      <ButtonGroup>
        <Button>One</Button>
      </ButtonGroup>
    );

    expect(screen.getByRole("group")).toHaveClass("flex-row");
  });

  it("should apply vertical orientation", () => {
    render(
      <ButtonGroup orientation="vertical">
        <Button>One</Button>
      </ButtonGroup>
    );

    expect(screen.getByRole("group")).toHaveClass("flex-col");
  });

  it("should apply gap when not attached", () => {
    render(
      <ButtonGroup>
        <Button>One</Button>
      </ButtonGroup>
    );

    expect(screen.getByRole("group")).toHaveClass("gap-2");
  });
});
