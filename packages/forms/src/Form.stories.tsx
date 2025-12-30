import type { Meta, StoryObj } from "@storybook/react";
import { Form, FormField, FormActions, FormSubmitButton } from "./Form";
import {
  ControlledInput,
  UncontrolledInput,
  FormTextarea,
  FormSelect,
  FormCheckbox,
} from "./components/FormInput";
import { useForm, FormProvider } from "react-hook-form";

const meta: Meta<typeof Form> = {
  title: "Forms/Form",
  component: Form,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component:
          "A form component with built-in validation support via React Hook Form.",
      },
    },
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Form>;

// Basic form example
export const BasicForm: Story = {
  render: () => {
    interface FormData {
      email: string;
      password: string;
    }

    const BasicFormComponent = () => {
      const methods = useForm<FormData>();

      const onSubmit = (data: FormData) => {
        alert(JSON.stringify(data, null, 2));
      };

      return (
        <FormProvider {...methods}>
          <Form onSubmit={methods.handleSubmit(onSubmit)} className="w-[400px]">
            <FormField
              name="email"
              label="Email"
              required
              description="We'll never share your email."
            >
              <ControlledInput
                name="email"
                control={methods.control}
                type="email"
                placeholder="you@example.com"
                rules={{ required: "Email is required" }}
              />
            </FormField>

            <FormField name="password" label="Password" required>
              <ControlledInput
                name="password"
                control={methods.control}
                type="password"
                placeholder="••••••••"
                rules={{
                  required: "Password is required",
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                }}
              />
            </FormField>

            <FormActions>
              <FormSubmitButton>Sign In</FormSubmitButton>
            </FormActions>
          </Form>
        </FormProvider>
      );
    };

    return <BasicFormComponent />;
  },
};

// Registration form with validation
export const RegistrationForm: Story = {
  render: () => {
    interface FormData {
      firstName: string;
      lastName: string;
      email: string;
      password: string;
      confirmPassword: string;
      terms: boolean;
    }

    const RegistrationFormComponent = () => {
      const methods = useForm<FormData>();
      const password = methods.watch("password");

      const onSubmit = (data: FormData) => {
        alert(JSON.stringify(data, null, 2));
      };

      return (
        <FormProvider {...methods}>
          <Form onSubmit={methods.handleSubmit(onSubmit)} className="w-[450px]">
            <div className="grid grid-cols-2 gap-4">
              <FormField name="firstName" label="First Name" required>
                <ControlledInput
                  name="firstName"
                  control={methods.control}
                  placeholder="John"
                  rules={{ required: "First name is required" }}
                />
              </FormField>

              <FormField name="lastName" label="Last Name" required>
                <ControlledInput
                  name="lastName"
                  control={methods.control}
                  placeholder="Doe"
                  rules={{ required: "Last name is required" }}
                />
              </FormField>
            </div>

            <FormField name="email" label="Email" required>
              <ControlledInput
                name="email"
                control={methods.control}
                type="email"
                placeholder="you@example.com"
                rules={{
                  required: "Email is required",
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: "Invalid email address",
                  },
                }}
              />
            </FormField>

            <FormField name="password" label="Password" required>
              <ControlledInput
                name="password"
                control={methods.control}
                type="password"
                placeholder="••••••••"
                rules={{
                  required: "Password is required",
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                }}
              />
            </FormField>

            <FormField name="confirmPassword" label="Confirm Password" required>
              <ControlledInput
                name="confirmPassword"
                control={methods.control}
                type="password"
                placeholder="••••••••"
                rules={{
                  required: "Please confirm your password",
                  validate: (value: string) =>
                    value === password || "Passwords do not match",
                }}
              />
            </FormField>

            <FormCheckbox
              name="terms"
              control={methods.control}
              label="I agree to the terms and conditions"
              rules={{ required: "You must agree to the terms" }}
            />

            <FormActions>
              <FormSubmitButton>Create Account</FormSubmitButton>
            </FormActions>
          </Form>
        </FormProvider>
      );
    };

    return <RegistrationFormComponent />;
  },
};

// Contact form with textarea
export const ContactForm: Story = {
  render: () => {
    interface FormData {
      name: string;
      email: string;
      subject: string;
      message: string;
    }

    const ContactFormComponent = () => {
      const methods = useForm<FormData>();

      const onSubmit = (data: FormData) => {
        alert(JSON.stringify(data, null, 2));
      };

      return (
        <FormProvider {...methods}>
          <Form onSubmit={methods.handleSubmit(onSubmit)} className="w-[450px]">
            <FormField name="name" label="Name" required>
              <ControlledInput
                name="name"
                control={methods.control}
                placeholder="Your name"
                rules={{ required: "Name is required" }}
              />
            </FormField>

            <FormField name="email" label="Email" required>
              <ControlledInput
                name="email"
                control={methods.control}
                type="email"
                placeholder="you@example.com"
                rules={{ required: "Email is required" }}
              />
            </FormField>

            <FormField name="subject" label="Subject" required>
              <FormSelect
                name="subject"
                control={methods.control}
                options={[
                  { value: "", label: "Select a subject" },
                  { value: "general", label: "General Inquiry" },
                  { value: "support", label: "Technical Support" },
                  { value: "billing", label: "Billing Question" },
                  { value: "feedback", label: "Feedback" },
                ]}
                rules={{ required: "Please select a subject" }}
              />
            </FormField>

            <FormField name="message" label="Message" required>
              <FormTextarea
                name="message"
                control={methods.control}
                placeholder="How can we help you?"
                rows={5}
                rules={{
                  required: "Message is required",
                  minLength: {
                    value: 20,
                    message: "Message must be at least 20 characters",
                  },
                }}
              />
            </FormField>

            <FormActions>
              <button
                type="button"
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <FormSubmitButton>Send Message</FormSubmitButton>
            </FormActions>
          </Form>
        </FormProvider>
      );
    };

    return <ContactFormComponent />;
  },
};

// Uncontrolled form example
export const UncontrolledForm: Story = {
  render: () => {
    const UncontrolledFormComponent = () => {
      const methods = useForm();

      const onSubmit = (data: Record<string, unknown>) => {
        alert(JSON.stringify(data, null, 2));
      };

      return (
        <FormProvider {...methods}>
          <Form onSubmit={methods.handleSubmit(onSubmit)} className="w-[400px]">
            <FormField name="username" label="Username">
              <UncontrolledInput
                {...methods.register("username", {
                  required: "Username is required",
                })}
                placeholder="Enter username"
              />
            </FormField>

            <FormField name="bio" label="Bio">
              <UncontrolledInput
                {...methods.register("bio")}
                placeholder="Tell us about yourself"
              />
            </FormField>

            <FormActions>
              <FormSubmitButton>Save</FormSubmitButton>
            </FormActions>
          </Form>
        </FormProvider>
      );
    };

    return <UncontrolledFormComponent />;
  },
};

// Form with all field types
export const AllFieldTypes: Story = {
  render: () => {
    interface FormData {
      text: string;
      email: string;
      password: string;
      number: number;
      select: string;
      textarea: string;
      checkbox: boolean;
    }

    const AllFieldsComponent = () => {
      const methods = useForm<FormData>();

      const onSubmit = (data: FormData) => {
        alert(JSON.stringify(data, null, 2));
      };

      return (
        <FormProvider {...methods}>
          <Form onSubmit={methods.handleSubmit(onSubmit)} className="w-[450px]">
            <FormField name="text" label="Text Input">
              <ControlledInput
                name="text"
                control={methods.control}
                placeholder="Enter text"
              />
            </FormField>

            <FormField name="email" label="Email Input">
              <ControlledInput
                name="email"
                control={methods.control}
                type="email"
                placeholder="you@example.com"
              />
            </FormField>

            <FormField name="password" label="Password Input">
              <ControlledInput
                name="password"
                control={methods.control}
                type="password"
                placeholder="••••••••"
              />
            </FormField>

            <FormField name="number" label="Number Input">
              <ControlledInput
                name="number"
                control={methods.control}
                type="number"
                placeholder="0"
              />
            </FormField>

            <FormField name="select" label="Select">
              <FormSelect
                name="select"
                control={methods.control}
                options={[
                  { value: "", label: "Choose an option" },
                  { value: "option1", label: "Option 1" },
                  { value: "option2", label: "Option 2" },
                  { value: "option3", label: "Option 3" },
                ]}
              />
            </FormField>

            <FormField name="textarea" label="Textarea">
              <FormTextarea
                name="textarea"
                control={methods.control}
                placeholder="Enter multiple lines..."
                rows={4}
              />
            </FormField>

            <FormCheckbox
              name="checkbox"
              control={methods.control}
              label="I agree to the terms"
            />

            <FormActions>
              <FormSubmitButton>Submit</FormSubmitButton>
            </FormActions>
          </Form>
        </FormProvider>
      );
    };

    return <AllFieldsComponent />;
  },
};
