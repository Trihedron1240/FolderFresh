# FolderFresh Documentation

Welcome to the FolderFresh documentation! This directory contains comprehensive guides for using and developing with FolderFresh.

---

## 📋 Table of Contents

### [Activity Log](./activity_log/)
Complete documentation for the Activity Log system that tracks all file operations.

- **[guide.md](./activity_log/guide.md)** - User guide and feature overview
- **[implementation.md](./activity_log/implementation.md)** - Technical implementation details

### [Dry Run Mode](./dry_run/)
Learn how to safely test rules and operations without making actual changes.

- **[dry_run_guide.md](./dry_run/dry_run_guide.md)** - Complete guide to dry-run mode functionality

### [Rules & Rule Engine](./rules/)
Documentation for creating, managing, and simulating rules.

- **[rule_persistence.md](./rules/rule_persistence.md)** - How rules are stored and loaded
- **[rule_simulator.md](./rules/rule_simulator.md)** - Test rules before applying them

### [Undo/Rollback System](./undo/)
Complete system for undoing file operations (move, rename, copy).

- **[undo_system_guide.md](./undo/undo_system_guide.md)** - Comprehensive undo system documentation
- **[quick_reference.txt](./undo/quick_reference.txt)** - Quick cheat sheet for common operations

### [User Interface](./ui/)
Guides for FolderFresh UI components and features.

- **[condition_list_ui.md](./ui/condition_list_ui.md)** - Condition list interface documentation

### [Validation](./validation/)
Data validation and safety checking documentation.

- **[validation_guide.md](./validation/validation_guide.md)** - Input validation and error handling

### [Watcher Integration](./watcher/)
Integration between the file watcher and rule engine.

- **[watcher_ruleengine_integration.md](./watcher/watcher_ruleengine_integration.md)** - How the watcher triggers rules

---

## 🚀 Quick Start

### For Users

1. **Learn the Basics**: Start with [Activity Log guide](./activity_log/guide.md)
2. **Create Rules**: See [Rule Engine documentation](./rules/)
3. **Test Safely**: Use [Dry Run Mode](./dry_run/dry_run_guide.md)
4. **Undo Operations**: Check [Undo System guide](./undo/undo_system_guide.md)

### For Developers

1. **System Architecture**: Read [Undo System guide](./undo/undo_system_guide.md) architecture section
2. **Rule Persistence**: Study [Rule Persistence](./rules/rule_persistence.md)
3. **Watcher Integration**: Review [Watcher Integration](./watcher/watcher_ruleengine_integration.md)
4. **Implementation Details**: Check [Activity Log Implementation](./activity_log/implementation.md)

---

## 📚 Feature Documentation

### Activity Log
- View all file operations performed by FolderFresh
- Track rule executions and undo operations
- Save logs for audit trails
- Real-time updates with timestamps

### Dry Run Mode
- Preview rule actions without making changes
- Test complex rule combinations safely
- Verify collision handling behavior
- Validate configurations before deployment

### Rules & Rule Engine
- Create conditions based on file properties (name, extension, size)
- Define actions (move, copy, rename)
- Set up rule matching (all/any conditions)
- Save and load rule profiles
- Simulate rule execution on test files

### Undo/Rollback
- Undo the last file operation
- Browse complete undo history
- Selectively undo specific operations
- Collision-safe restoration
- Dry-run aware (doesn't record preview operations)

### File Watcher
- Automatically trigger rules on file changes
- Monitor specified directories
- Real-time rule execution
- Undo watcher-initiated operations

### Validation
- Input validation for file paths
- Configuration validation
- Error detection and reporting
- Safe mode collision handling

---

## 🔍 Common Tasks

### How do I undo an operation?
See [Undo System - Usage section](./undo/undo_system_guide.md#usage)

### How do I test rules before applying them?
See [Dry Run Mode guide](./dry_run/dry_run_guide.md)

### How do I understand what operations were performed?
See [Activity Log guide](./activity_log/guide.md)

### How do I set up automatic rule execution?
See [Watcher Integration guide](./watcher/watcher_ruleengine_integration.md)

### How do I create and manage rules?
See [Rule Persistence guide](./rules/rule_persistence.md)

---

## ⚙️ Advanced Topics

### Architecture
- [Undo System Architecture](./undo/undo_system_guide.md#architecture)
- [Rule Engine Design](./rules/rule_persistence.md)
- [Watcher-Rule Integration](./watcher/watcher_ruleengine_integration.md)

### Performance
- [Undo System Performance](./undo/undo_system_guide.md#performance)
- [Activity Log Optimization](./activity_log/implementation.md)

### Safety & Error Handling
- [Undo System Safety Features](./undo/undo_system_guide.md#safety-features)
- [Collision Handling](./undo/undo_system_guide.md#collision-safety)
- [Validation Guide](./validation/validation_guide.md)

### Configuration
- [Rule Configuration](./rules/rule_persistence.md)
- [Undo Stack Configuration](./undo/undo_system_guide.md#configuration)
- [Dry Run Configuration](./dry_run/dry_run_guide.md)

---

## 🐛 Troubleshooting

- **Activity Log Issues**: See [Activity Log guide - Troubleshooting](./activity_log/guide.md#troubleshooting)
- **Undo Not Working**: See [Undo System guide - Troubleshooting](./undo/undo_system_guide.md#troubleshooting)
- **Rule Execution Problems**: See [Rule Persistence guide](./rules/rule_persistence.md)
- **Watcher Issues**: See [Watcher Integration guide](./watcher/watcher_ruleengine_integration.md)

---

## 📖 Documentation Map

```
docs/
├── README.md (you are here)
├── activity_log/
│   ├── guide.md
│   └── implementation.md
├── dry_run/
│   └── dry_run_guide.md
├── rules/
│   ├── rule_persistence.md
│   └── rule_simulator.md
├── undo/
│   ├── undo_system_guide.md
│   └── quick_reference.txt
├── ui/
│   └── condition_list_ui.md
├── validation/
│   └── validation_guide.md
└── watcher/
    └── watcher_ruleengine_integration.md
```

---

## 🔗 Additional Resources

- **Project Repository**: https://github.com/yourusername/folderfresh
- **Issue Tracker**: https://github.com/yourusername/folderfresh/issues
- **Main README**: [../README.md](../README.md)
- **Tests**: [../tests/](../tests/)

---

## 📝 Documentation Standards

All documentation in this directory follows these standards:

- **Markdown Format**: All docs use standard Markdown
- **Clear Structure**: Sections use consistent heading hierarchy
- **Code Examples**: Practical, runnable examples included
- **Visual Aids**: Diagrams and ASCII art for clarity
- **Cross-references**: Links between related topics
- **Comprehensive**: Covers user and developer perspectives

---

## 🆘 Need Help?

1. **Search this documentation** using Ctrl+F
2. **Check the main README** for project overview
3. **Review test files** for usage examples
4. **File an issue** on GitHub for bugs or feature requests

---

## 📋 Document Descriptions

### Activity Log Documentation
Covers logging of all file operations, undo actions, and provides audit trails. Includes both user guide and technical implementation details.

### Dry Run Mode Documentation
Explains how to safely test rule configurations without modifying files, essential for validating complex rule sets before deployment.

### Rule Engine Documentation
Documents rule creation, persistence to disk, loading from profiles, and the simulator for testing rules on sample files.

### Undo System Documentation
Comprehensive guide to reversing file operations, architectural details, collision handling, and safety guarantees.

### UI Documentation
User interface guides for condition list selection and other UI components.

### Validation Documentation
Technical reference for input validation, error handling, and safety features throughout the application.

### Watcher Integration Documentation
How the file watcher interacts with the rule engine to automatically trigger rules on file system events.

---

**Last Updated**: 2025-11-28
**Status**: ✅ Complete and Production-Ready
