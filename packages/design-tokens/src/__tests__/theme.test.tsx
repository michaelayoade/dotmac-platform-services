import { render, screen, act } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../theme";

// Mock matchMedia
const createMatchMedia = (matches: boolean) => {
  return jest.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
};

describe("ThemeProvider", () => {
  beforeEach(() => {
    // Reset matchMedia to default (light mode, no reduced motion)
    window.matchMedia = createMatchMedia(false);
    // Clear any classes on documentElement
    document.documentElement.className = "";
  });

  it("should provide theme context to children", () => {
    const TestComponent = () => {
      const { config } = useTheme();
      return <div data-testid="variant">{config.variant}</div>;
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("variant")).toHaveTextContent("admin");
  });

  it("should use custom default variant", () => {
    const TestComponent = () => {
      const { config } = useTheme();
      return <div data-testid="variant">{config.variant}</div>;
    };

    render(
      <ThemeProvider defaultVariant="customer">
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("variant")).toHaveTextContent("customer");
  });

  it("should update variant via setVariant", () => {
    const TestComponent = () => {
      const { config, setVariant } = useTheme();
      return (
        <div>
          <div data-testid="variant">{config.variant}</div>
          <button onClick={() => setVariant("reseller")}>Change</button>
        </div>
      );
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("variant")).toHaveTextContent("admin");

    act(() => {
      screen.getByText("Change").click();
    });

    expect(screen.getByTestId("variant")).toHaveTextContent("reseller");
  });

  it("should apply dark class when colorScheme is dark", () => {
    render(
      <ThemeProvider defaultColorScheme="dark">
        <div>Test</div>
      </ThemeProvider>
    );

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("should not apply dark class when colorScheme is light", () => {
    render(
      <ThemeProvider defaultColorScheme="light">
        <div>Test</div>
      </ThemeProvider>
    );

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("should respond to system color scheme preference", () => {
    // Mock dark mode preference
    window.matchMedia = createMatchMedia(true);

    const TestComponent = () => {
      const { resolvedColorScheme, isDarkMode } = useTheme();
      return (
        <div>
          <div data-testid="resolved">{resolvedColorScheme}</div>
          <div data-testid="isDark">{isDarkMode ? "yes" : "no"}</div>
        </div>
      );
    };

    render(
      <ThemeProvider defaultColorScheme="system">
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
    expect(screen.getByTestId("isDark")).toHaveTextContent("yes");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("should detect reduced motion preference", () => {
    // Mock reduced motion preference
    window.matchMedia = jest.fn().mockImplementation((query: string) => ({
      matches: query.includes("prefers-reduced-motion"),
      media: query,
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    const TestComponent = () => {
      const { config } = useTheme();
      return (
        <div data-testid="reducedMotion">
          {config.reducedMotion ? "yes" : "no"}
        </div>
      );
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("reducedMotion")).toHaveTextContent("yes");
  });

  it("should update density via setDensity", () => {
    const TestComponent = () => {
      const { config, setDensity } = useTheme();
      return (
        <div>
          <div data-testid="density">{config.density}</div>
          <button onClick={() => setDensity("compact")}>Compact</button>
        </div>
      );
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId("density")).toHaveTextContent("comfortable");

    act(() => {
      screen.getByText("Compact").click();
    });

    expect(screen.getByTestId("density")).toHaveTextContent("compact");
  });

  it("should apply CSS variables to document root", () => {
    render(
      <ThemeProvider>
        <div>Test</div>
      </ThemeProvider>
    );

    const root = document.documentElement;

    // Check that some CSS variables are set
    expect(root.style.getPropertyValue("--color-primary-500")).toBeTruthy();
    expect(root.style.getPropertyValue("--font-family-sans")).toBeTruthy();
  });

  it("should generate theme classes", () => {
    const TestComponent = () => {
      const { getThemeClasses } = useTheme();
      return <div data-testid="classes">{getThemeClasses()}</div>;
    };

    render(
      <ThemeProvider defaultVariant="customer" defaultDensity="compact">
        <TestComponent />
      </ThemeProvider>
    );

    const classes = screen.getByTestId("classes").textContent;
    expect(classes).toContain("theme-customer");
    expect(classes).toContain("density-compact");
    expect(classes).toContain("color-light");
  });

  it("should throw error when useTheme is used outside provider", () => {
    const TestComponent = () => {
      useTheme();
      return <div>Test</div>;
    };

    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow("useTheme must be used within a ThemeProvider");

    consoleSpy.mockRestore();
  });

  it("should update config via updateConfig", () => {
    const TestComponent = () => {
      const { config, updateConfig } = useTheme();
      return (
        <div>
          <div data-testid="variant">{config.variant}</div>
          <div data-testid="density">{config.density}</div>
          <button
            onClick={() =>
              updateConfig({ variant: "technician", density: "spacious" })
            }
          >
            Update
          </button>
        </div>
      );
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    act(() => {
      screen.getByText("Update").click();
    });

    expect(screen.getByTestId("variant")).toHaveTextContent("technician");
    expect(screen.getByTestId("density")).toHaveTextContent("spacious");
  });

  it("should provide portal color scheme", () => {
    const TestComponent = () => {
      const { portalScheme } = useTheme();
      return <div data-testid="accent">{portalScheme.accent}</div>;
    };

    render(
      <ThemeProvider defaultVariant="admin">
        <TestComponent />
      </ThemeProvider>
    );

    // Admin accent color should be present
    expect(screen.getByTestId("accent").textContent).toBeTruthy();
  });
});
