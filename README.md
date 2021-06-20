# prify #

`prify` is a tool to support a phabricator style patch review workflow within github.

## How it Works ##

There are [Many Great Resources](https://www.google.com/search?q=git+rewrite+history) on how to rewrite history,
and the pros/cons of a [patch based review](https://www.spreedly.com/blog/merge-pull-request-considered-harmful#.VcT5PbeC26A)
vs [PR](https://guides.github.com/introduction/flow/). For those who like the former it's something of an art form. Broadly
speaking, this follows the 'commit per logical feature' approach.

Let's say you have the following commits as show in `git rebase -i` on your local `dev` branch

```
pick 39ba2d9f Feature A
pick b50a35a6 Feature B
```

You would re-write history, running prify after each commit you'd like to have as a PR.

```
pick 39ba2d9f Feature A
x prify sync
pick b50a35a6 Feature B
x prify sync
```

This would create the following branches with corresonding PRs + Commits (assuming the local user is jeeva)

```
dev
 - 39ba2d9f Feature A
 - b50a35a6 Feature B

jeeva-feature-a
 - 39ba2d9f Feature A

jeeva-feature-b
 - b50a35a6 Feature B
```

Now, as part of the review cycle, you are asked to make changes to both PRs. You would do these on your local branch

```
pick d105e0ff fixup for feature B as requested byb reviewer
pick 6be5916d fixup for feature A as requested by reviewer
pick 39ba2d9f Feature A
pick b50a35a6 Feature B
```

Then squash these back into the main feature commits, running prify after each

```
pick 39ba2d9f Feature A
f 6be5916d fixup for feature A as requested by reviewer
x prify sync
pick b50a35a6 Feature B
f d105e0ff fixup for feature B as requested byb reviewer
x prify sync fixup as requested by @timbod
```

This would result in the following local updated local dev and feature branches.

```
dev
 - 80c9670c Feature A
 - 8e4b96d7 Feature B

jeeva-feature-a
 - 39ba2d9f Feature A
 - 00faa529 updates

jeeva-feature-b
 - b50a35a6 Feature B
 - f58bf0b9 fixups as requested by @timbod
```

Importantly, history isn't re-written on the feature branches (same commit hash), this keeps PR comment history in tact, so it's easy for a reviewer to
track if their comments have been addressed.

Same process is followed when re-basing local dev onto remote main. Given this is a common enough use-case, after a rebase run

`prify update-from-remote`. This will (for each feature commit). Sync with corresponding feature branch and push. The new commit will
have the default subject `update from remote`. In this case, we'll end up with the following local dev and feature branches

```
dev
 - 90c9670c Feature A
 - 9e4b96d7 Feature B

jeeva-feature-a
 - 39ba2d9f Feature A
 - 00faa529 updates
 - 93ba2a9f update from remote

jeeva-feature-b
 - b50a35a6 Feature B
 - f58bf0b9 fixups as requested by @timbod
 - 9f1cf0b9 update from remote
```

Notice again history hasn't been re-written on any feature branch.

Now, when you are ready to land features, you run `prify show-landable`. This will have the following output

```
✅ 90c9670c Feature A
❌ 9e4b96d7 Feature B
✏️  fe32fe12 Feature C
```

Meaning Feature A is landable, Feature B is blocked by the reviewer and Feature C is currently in review. Running
`prify land` will then.

   1. Ensure the commit on local dev the feature branch result in the same diff.
   2. Squash merge the PR.
   3. Replace the local commit with what's been merged onto main
   4. Repeat steps (1-3) for each landable feature in order (stopping once we hit a feature in review or blocked)

