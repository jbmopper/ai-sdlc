# Desires for AI Development Workflow
 - documents are cleaned up and don't accumulate
 - changes are committed and merged in frequently; agents wrap worktrees up and fold back into the main project and clean up after themselves proactively
 - agents don't look at old documents and pollute themselves
 - agents don't propagate errors and misquoted context through additional calls and steps
 - requirements are remembered and adhered to
 - when requirements are translated into prompts they are consistent with the directions, strategies and requirements of the project
 - items that are flagged for future discovery or as waiting to be specified as part of future work get surfaced to the user when work is being done
 - outputs are complete yet minimal.  Outputs to users use full sentences and avoid jargon and fragments while being minimal.  Prompts are similarly complete yet minimal.  Code is minimal.
 - tests coverage is explained and tests make sense and matter
 - small bugs and corner cases are cataloged and surfaced before being worked on.  Surfacing may be to a coordinator agent or preferably the user.  The goal is code that's solid enough for velocity, not completely clean but burning tokens
 - questions about the overall design and goal of the project are raised during discovery and design phases

# Phases
 - global telos: how does the project fit into the user's overall priorities?  This guides scope and effort.
 - 