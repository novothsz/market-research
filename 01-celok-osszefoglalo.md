# Project Goal Summary

## Goal
The goal of this project is to build a job search system that is easy to run and can collect, analyze, and rank relevant job postings based on the user's professional background and a separately defined search objective.

The system should be especially useful for hard-to-find roles, such as reinforcement learning jobs in Hungary or Hungarian-related positions that are also available remotely from Hungary.

## Core Problem
Based on user experience, traditional keyword search, especially on LinkedIn, is often misleading.

Many results contain "reinforcement learning" or other relevant keywords in the title or highlighted fields, but after reading the full job description, the role turns out not to be RL-focused, or only loosely related.

So the main problem is not only finding job postings, but evaluating their content quality and deciding their true relevance.

## Expected Behavior
Ideally, the system should be able to:

- Ingest the user's professional profile from sources like exported or pasted LinkedIn text, CV text, or manually provided background details.
- Accept a separate prompt or search description that defines the exact type of roles to find.
- Collect job links and full descriptions from multiple sources.
- Analyze the full description, not only the title or summary snippet.
- Decide whether a posting is actually relevant to the target objective.
- Explain briefly why a position is relevant or not relevant.
- Rank results against both the user profile and the goal described in the prompt.

## Functional Expectations
The system should be general, not tied only to reinforcement learning. It should support any professional search theme when the user provides a new prompt.

The system must clearly separate these two inputs:

- Static professional background: the user's history, experience, and skills.
- Current search objective: the exact type of role the user wants right now.

This is important because the same profile may be used for multiple search objectives.

## Technology Preferences
There is an explicit preference that the solution should be as Python-based as possible.

If possible, the implementation should rely only on Python and the uv package manager, minimizing extra environment dependencies, additional installed tools, or a multi-language stack.

This means unnecessary Node.js layers, separate frontend build systems, or other non-essential technology layers should be avoided.

## Development Usage
This document is intended as input for code-generating agents, especially Claude Code and GitHub Copilot.

Because of that, the wording should make it clear that the task is not just to build a scraper, but to implement a multi-step job collection and relevance evaluation pipeline.
