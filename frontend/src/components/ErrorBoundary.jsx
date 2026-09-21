import React from "react";

export default class ErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <pre style={{ color: "#ff8a8a", background: "#111", padding: 24, whiteSpace: "pre-wrap" }}>
          {String(this.state.error.stack || this.state.error)}
        </pre>
      );
    }
    return this.props.children;
  }
}