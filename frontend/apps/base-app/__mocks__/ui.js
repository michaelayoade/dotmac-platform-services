const React = require('react');

const Card = ({ children }) => React.createElement('div', {}, children);
Card.Header = ({ children }) => React.createElement('div', {}, children);
Card.Content = ({ children }) => React.createElement('div', {}, children);
Card.Title = ({ children }) => React.createElement('h3', {}, children);
Card.Description = ({ children }) => React.createElement('p', {}, children);

module.exports = {
  Button: ({ children, onClick }) => React.createElement('button', { onClick }, children),
  Card: Card,
  CardHeader: Card.Header,
  CardContent: Card.Content,
  CardTitle: Card.Title,
  Alert: ({ children }) => React.createElement('div', {}, children),
  Skeleton: () => React.createElement('div', {}, 'Loading...'),
}