import { render, screen, fireEvent } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "../primitives/Card";

describe("Card", () => {
  it("should render children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("should apply default variant classes", () => {
    render(<Card>Card</Card>);
    const card = screen.getByText("Card");
    expect(card).toHaveClass("shadow-sm");
  });

  it("should apply elevated variant classes", () => {
    render(<Card variant="elevated">Elevated</Card>);
    const card = screen.getByText("Elevated");
    expect(card).toHaveClass("shadow-md");
  });

  it("should apply outlined variant classes", () => {
    render(<Card variant="outlined">Outlined</Card>);
    const card = screen.getByText("Outlined");
    expect(card).toHaveClass("shadow-none");
  });

  it("should apply ghost variant classes", () => {
    render(<Card variant="ghost">Ghost</Card>);
    const card = screen.getByText("Ghost");
    expect(card).toHaveClass("border-transparent", "bg-transparent");
  });

  it("should apply padding variants", () => {
    render(<Card padding="lg">Large Padding</Card>);
    const card = screen.getByText("Large Padding");
    expect(card).toHaveClass("p-6");
  });

  it("should apply no padding", () => {
    render(<Card padding="none">No Padding</Card>);
    const card = screen.getByText("No Padding");
    expect(card).not.toHaveClass("p-4");
    expect(card).not.toHaveClass("p-3");
  });

  it("should apply interactive classes", () => {
    render(<Card interactive>Interactive</Card>);
    const card = screen.getByText("Interactive");
    expect(card).toHaveClass("cursor-pointer");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<Card ref={ref}>Ref Card</Card>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("should apply custom className", () => {
    render(<Card className="custom-class">Custom</Card>);
    expect(screen.getByText("Custom")).toHaveClass("custom-class");
  });

  it("should handle click events when interactive", () => {
    const handleClick = jest.fn();
    render(
      <Card interactive onClick={handleClick}>
        Clickable
      </Card>
    );

    fireEvent.click(screen.getByText("Clickable"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("CardHeader", () => {
  it("should render children", () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText("Header content")).toBeInTheDocument();
  });

  it("should apply default classes", () => {
    render(<CardHeader>Header</CardHeader>);
    const header = screen.getByText("Header");
    expect(header).toHaveClass("p-4", "pb-0");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<CardHeader ref={ref}>Header</CardHeader>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("should apply custom className", () => {
    render(<CardHeader className="custom-header">Header</CardHeader>);
    expect(screen.getByText("Header")).toHaveClass("custom-header");
  });
});

describe("CardTitle", () => {
  it("should render children", () => {
    render(<CardTitle>Title</CardTitle>);
    expect(screen.getByText("Title")).toBeInTheDocument();
  });

  it("should render as h3 by default", () => {
    render(<CardTitle>Title</CardTitle>);
    expect(screen.getByRole("heading", { level: 3 })).toBeInTheDocument();
  });

  it("should render as specified heading level", () => {
    render(<CardTitle as="h1">Title</CardTitle>);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("should apply typography classes", () => {
    render(<CardTitle>Title</CardTitle>);
    const title = screen.getByText("Title");
    expect(title).toHaveClass("text-lg", "font-semibold");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<CardTitle ref={ref}>Title</CardTitle>);
    expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
  });

  it("should apply custom className", () => {
    render(<CardTitle className="custom-title">Title</CardTitle>);
    expect(screen.getByText("Title")).toHaveClass("custom-title");
  });
});

describe("CardDescription", () => {
  it("should render children", () => {
    render(<CardDescription>Description text</CardDescription>);
    expect(screen.getByText("Description text")).toBeInTheDocument();
  });

  it("should apply muted text classes", () => {
    render(<CardDescription>Description</CardDescription>);
    const description = screen.getByText("Description");
    expect(description).toHaveClass("text-muted-foreground");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<CardDescription ref={ref}>Description</CardDescription>);
    expect(ref.current).toBeInstanceOf(HTMLParagraphElement);
  });

  it("should apply custom className", () => {
    render(
      <CardDescription className="custom-desc">Description</CardDescription>
    );
    expect(screen.getByText("Description")).toHaveClass("custom-desc");
  });
});

describe("CardContent", () => {
  it("should render children", () => {
    render(<CardContent>Content here</CardContent>);
    expect(screen.getByText("Content here")).toBeInTheDocument();
  });

  it("should apply default padding classes", () => {
    render(<CardContent>Content</CardContent>);
    const content = screen.getByText("Content");
    expect(content).toHaveClass("p-4", "pt-0");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<CardContent ref={ref}>Content</CardContent>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("should apply custom className", () => {
    render(<CardContent className="custom-content">Content</CardContent>);
    expect(screen.getByText("Content")).toHaveClass("custom-content");
  });
});

describe("CardFooter", () => {
  it("should render children", () => {
    render(<CardFooter>Footer content</CardFooter>);
    expect(screen.getByText("Footer content")).toBeInTheDocument();
  });

  it("should apply flex and padding classes", () => {
    render(<CardFooter>Footer</CardFooter>);
    const footer = screen.getByText("Footer");
    expect(footer).toHaveClass("flex", "items-center", "p-4", "pt-0");
  });

  it("should forward ref", () => {
    const ref = { current: null };
    render(<CardFooter ref={ref}>Footer</CardFooter>);
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it("should apply custom className", () => {
    render(<CardFooter className="custom-footer">Footer</CardFooter>);
    expect(screen.getByText("Footer")).toHaveClass("custom-footer");
  });
});

describe("Card Composition", () => {
  it("should compose all card parts correctly", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card description text</CardDescription>
        </CardHeader>
        <CardContent>Main content goes here</CardContent>
        <CardFooter>Footer actions</CardFooter>
      </Card>
    );

    expect(screen.getByRole("heading", { name: /card title/i })).toBeInTheDocument();
    expect(screen.getByText("Card description text")).toBeInTheDocument();
    expect(screen.getByText("Main content goes here")).toBeInTheDocument();
    expect(screen.getByText("Footer actions")).toBeInTheDocument();
  });
});
