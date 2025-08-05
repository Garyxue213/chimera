# Contributing to Project Chimera

Thank you for your interest in contributing to Project Chimera! This project focuses on AI safety research, specifically studying deceptive behavior in multi-agent systems and developing monitoring mechanisms to detect such behavior.

## Code of Conduct

This project is committed to providing a welcoming and inclusive environment for all contributors. We ask that all participants adhere to professional and respectful communication standards.

## Getting Started

1. **Fork the repository** and clone your fork locally
2. **Set up the development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Copy the environment template**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Types of Contributions

### 🐛 Bug Reports
- Use the issue template to report bugs
- Include detailed steps to reproduce
- Provide system information and logs when relevant

### 💡 Feature Requests
- Clearly describe the proposed feature
- Explain the use case and potential impact
- Consider AI safety implications

### 🔧 Code Contributions
- Follow the existing code style and structure
- Add tests for new functionality
- Update documentation as needed
- Ensure ethical considerations are addressed

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all public functions and classes
- Keep functions focused and relatively small

### Testing
- Write unit tests for new functionality
- Run the existing test suite before submitting
- Include integration tests for complex features

### Documentation
- Update the README.md if you change core functionality
- Add inline comments for complex logic
- Update docstrings when modifying functions

## AI Safety Considerations

Given the nature of this project, special care must be taken when contributing:

### Ethical Guidelines
- **No Real-World Harm**: All deceptive behaviors must be contained within the simulation
- **Research Purpose Only**: Features should advance AI safety research
- **Responsible Disclosure**: Any discovered vulnerabilities should be reported responsibly
- **Clear Documentation**: Make the research purpose and limitations clear

### Security Considerations
- Never include real API keys or sensitive data
- Ensure simulated "attacks" cannot escape the sandbox
- Document potential risks of new features
- Consider the implications of publishing certain techniques

## Submission Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, well-documented code
   - Add appropriate tests
   - Update documentation

3. **Test your changes**:
   ```bash
   python -m pytest
   python3 run_hierarchical_simulation.py --steps 5 --scenario "Test scenario"
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature: brief description of what you added"
   ```

5. **Push and create a pull request**:
   - Provide a clear description of your changes
   - Reference any related issues
   - Explain the AI safety implications (if any)

## Review Process

All contributions will be reviewed for:
- **Code Quality**: Adherence to style guidelines and best practices
- **Functionality**: Does it work as intended?
- **Safety**: Are there any security or ethical concerns?
- **Documentation**: Is it well-documented and clear?
- **Testing**: Are there adequate tests?

## Questions or Help

If you have questions about contributing:
- Check existing issues and discussions
- Create a new issue with the "question" label
- Reach out to the maintainers

## Recognition

Contributors will be acknowledged in the project documentation and any resulting research publications (with permission).

---

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.
