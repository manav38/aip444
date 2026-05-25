# Week 3 - Effective Prompt Engineering

## Overview

1. Prompt Engineering
2. Anatomy of a Prompt
   1. Instructions
   2. Context
   3. User and Assistant messages
3. The power and nuance of System Prompts and how to "steer" models
4. Organizing prompts using inline delimiters, use of structured text, examples and non-examples
5. Common prompt techniques: zero-shot, few-shot, chain-of-thought, etc.

## Prompt Engineering

Last week we learned about the various **roles** that `messages` can have in chat completions, specifically looking at `user` and `assistant` messages. This week our focus will be on the `system` and `user` roles, and how to use them effectively.

We'll often refer to both the `system` and `user` messages as **prompts**, and the techniques we'll discuss today as **prompt engineering**. The use of the term **engineering** here refers to the fact that we will try to be systematic in our approach, carefully testing things, iterating, versioning, and optimizing as we go. Even though we will work in natural language vs. code, the same principles of good software engineering apply.

## Strategies for Iterating on Prompts

The lifecycle of a prompt has two main stages:

1. **Initial research phase** - during which we experiment with, develop, and test our prompt, improving until it becomes more reliable.
2. **Production phase** - during which we deploy and use our prompt in an application.

Moving from research to production involves a number of steps:

1. **Test with Real Users:** Give your prompts to people without context and gather feedback.
2. **Document Everything:** Track prompt versions, configurations, and performance metrics.
3. **Learn from Failures:** Each failure provides information for improving the next version.
4. **A/B Testing:** Compare different approaches systematically.
5. **Edge Case Discovery:** Actively seek out scenarios where your prompt fails.

Prompting is fundamentally about clear communication combined with systematic engineering practices.

## Production Prompts

After a period of research and experimentation, we will have enough data to know how the model is likely to respond and what is possible. We will write instructions that include extensive examples for consistency and use real-world data, representing the types of edge cases we experienced during testing.

At this stage we are optimizing for repeated use at scale, and reliability and safety are both important.

## Prompts and Cost

As prompts grow in length, we have to keep one eye on token usage and costs. The ability of a model can also degrade as prompts grow large, especially for models with smaller context windows.

Figuring out the right model, prompt length, and cost will be part of your work to production-ize your prompts.

## System Prompt

System prompts provide instructions to the model. They are used to give background context and rules for responding, and offer the model insights into what the conversation is about.

System prompts often include things like:

- **Behavioural Suggestions** - the AI's personality, level of expertise, role in the chat
- **Response Constraints** - rules about what to do or not do when responding
- **Background Information** - assumed context that is necessary for performing tasks
- **Reasoning Instructions** - how the AI should approach complex problems
- **Edge Case Handling** - what to do when inputs are unclear, corrupted, or outside expected parameters

The system prompt is a tool for improving the consistency and relevance of responses for a repeated task.

## What to Include in a System Prompt?

### Role

LLMs generally perform better when you include a specific role for the LLM to follow. By shaping the role that the LLM assumes, system prompts help enhance accuracy, tailor the tone, and keep the answer from straying into irrelevant information.

### Background Context

The system prompt is useful for including background information that users will assume and the LLM should understand.

### Response Structure, Format, and Style

If the response needs to follow a particular format, let the LLM know by showing it a template and ideally a few examples.

### Reasoning and Problem Solving

Modern LLMs do better when they can reason or think before responding. Reasoning instructions help embed dynamic context into the system prompt.

Examples include:

- Chain-of-thought prompting
- Step-back prompting
- Self-consistency checks

### Failure Cases

Always include instructions for the LLM to follow when the user input does not follow the expected pattern.

Failure handling can include:

- Input validation
- Boundary enforcement
- Data quality issue handling

## System Prompt Structure and Organization

A helpful template for organizing a system prompt is:

# Role and Objective
[Who the AI is and what it's trying to accomplish]

# Background Context
[Relevant information and data]

# Instructions
[High-level rules and guidelines]

## Response Format
[Specific formatting requirements]

## Reasoning Approach
[How to handle complex problems]

## Edge Case Handling
[What to do when things go wrong]

# Examples
[A few examples of inputs and outputs to use as a guide]

# Final Instructions
[Reinforcement and repetition of key points]

## Delimiter Best Practices

Markdown is recommended for structuring prompts. Use headers, inline backticks, fenced code blocks, lists, bold text, and horizontal rules.

XML is also effective for precise content wrapping and separating large sections of mixed content.

## Assistant and User Messages

A user message can come from user input, documents, database queries, or other program output. User input has risks because malicious users can use prompt injection to override instructions.

Properly delimiting and identification of user input vs. instructions in a prompt is critical.

## Creative Message Use: Simulated Message History

Examples can be included as fake user and assistant messages in the conversation history. This helps chat-optimized models distinguish between global rules and execution patterns.

## Creative Message Use: Pre-filling

Pre-filling the model's response can help enforce formats and prevent conversational filler.

## Common Prompting Techniques

### Zero-Shot Prompting

With zero-shot prompting, you describe a task for the model to perform without any examples for how to respond. It is fast to develop and cheaper to run, but it is the least reliable method for complex formatting or nuanced tasks.

### Few-Shot Prompting

When a model struggles to understand instructions or consistently fails to output the specific format needed, few-shot prompting is usually the next technique to try.

Few-shot prompting means providing a few examples of the task being performed correctly within the prompt context.

This technique leverages the model's pattern-matching abilities. Instead of telling it only what to do, you show it how to do it correctly.

### Chain-of-Thought Prompting

Chain-of-thought prompting encourages the model to show its work before presenting the final answer. By generating intermediate reasoning steps, the model creates context that helps it derive the correct answer.

A simple trigger is: "Let's think step by step."

### Generated Knowledge Prompting

Generated knowledge prompting asks the model to generate facts or knowledge about a topic first, then use that generated knowledge to answer the original question.

### Rephrase and Respond

Rephrase and Respond instructs the model to reinterpret the user's intent, expand it, and then answer the improved version of the question.

### Chain of Density

Chain of Density is an iterative prompt technique that asks the model to rewrite a summary multiple times, adding more important entities each time without increasing the word count.

## Advanced Reasoning Strategies

For complex applications, structured reasoning strategies can be included in the system prompt. A workflow may include:

1. Query Analysis
2. Context Analysis
3. Synthesis

By explicitly defining mental steps in the workflow, we move from simple text generation to simulated reasoning, resulting in more reliable outputs.

## Conclusion

Effective prompt engineering is fundamentally about clear communication combined with systematic iteration.

1. **Prompts are code**: Treat them with the same rigor as any other software artifact.
2. **Specificity matters**: The more precisely you define the task, format, and constraints, the more consistent your results will be.
3. **Context is king**: Giving the model the right context dramatically improves output quality.
4. **No silver bullets**: Prompt engineering remains experimental. Always test with your specific use case.