~/workspace$ echo "# CAD-Analyzer-Pro-V-4" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/rehmanul/CAD-Analyzer-Pro-V-4.git
git push -u origin main
Reinitialized existing Git repository in /home/runner/workspace/.git/
[main aa0e28e] first commit
 1 file changed, 1 insertion(+)
error: remote origin already exists.
Enumerating objects: 227, done.
Counting objects: 100% (227/227), done.
Delta compression using up to 8 threads
Compressing objects: 100% (182/182), done.
Writing objects: 100% (227/227), 3.68 MiB | 3.22 MiB/s, done.
Total 227 (delta 122), reused 100 (delta 42), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (122/122), done.
remote: fatal: did not receive expected object 8e04b62c4ac7baf7e3896a8d6159668ca66069c5
error: remote unpack failed: index-pack failed
To https://github.com/rehmanul/CAD-Analyzer-Pro-V-4
 ! [remote rejected] main -> main (failed)
error: failed to push some refs to 'https://github.com/rehmanul/CAD-Analyzer-Pro-V-4'
~/workspace$ git remote add origin https://github.com/rehmanul/CAD-Analyzer-Pro-V-4.git
git branch -M main
git push -u origin main
error: remote origin already exists.
Enumerating objects: 227, done.
Counting objects: 100% (227/227), done.
Delta compression using up to 8 threads
Compressing objects: 100% (182/182), done.
Writing objects: 100% (227/227), 3.68 MiB | 5.94 MiB/s, done.
Total 227 (delta 121), reused 100 (delta 42), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (121/121), done.
remote: fatal: did not receive expected object 8e04b62c4ac7baf7e3896a8d6159668ca66069c5
error: remote unpack failed: index-pack failed
To https://github.com/rehmanul/CAD-Analyzer-Pro-V-4
 ! [remote rejected] main -> main (failed)
error: failed to push some refs to 'https://github.com/rehmanul/CAD-Analyzer-Pro-V-4'
~/workspace$ git init
Reinitialized existing Git repository in /home/runner/workspace/.git/
~/workspace$ git add .
~/workspace$ git commit "first"
error: pathspec 'first' did not match any file(s) known to git
~/workspace$ git commit "ok"
error: pathspec 'ok' did not match any file(s) known to git
~/workspace$ git commit
On branch main
Your branch is ahead of 'origin/main' by 23 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
~/workspace$ git push
Enumerating objects: 227, done.
Counting objects: 100% (227/227), done.
Delta compression using up to 8 threads
Compressing objects: 100% (182/182), done.
Writing objects: 100% (227/227), 3.68 MiB | 3.43 MiB/s, done.
Total 227 (delta 121), reused 100 (delta 42), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (121/121), done.
remote: fatal: did not receive expected object 8e04b62c4ac7baf7e3896a8d6159668ca66069c5
error: remote unpack failed: index-pack failed
To https://github.com/rehmanul/CAD-Analyzer-Pro-V-4
 ! [remote rejected] main -> main (failed)
error: failed to push some refs to 'https://github.com/rehmanul/CAD-Analyzer-Pro-V-4'
~/workspace$ git pull origin main   # Pull the latest changes from the main branch
# Resolve any merge conflicts if they arise
git add .              # Stage your resolved files
git commit -m "Resolved merge conflicts"  # Commit your changes
git push origin main   # Attempt to push your changes again
fatal: couldn't find remote ref main
On branch main
Your branch is ahead of 'origin/main' by 23 commits.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
Enumerating objects: 227, done.
Counting objects: 100% (227/227), done.
Delta compression using up to 8 threads
Compressing objects: 100% (182/182), done.
Writing objects: 100% (227/227), 3.68 MiB | 3.07 MiB/s, done.
Total 227 (delta 122), reused 100 (delta 42), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (122/122), done.
remote: fatal: did not receive expected object 8e04b62c4ac7baf7e3896a8d6159668ca66069c5
error: remote unpack failed: index-pack failed
To https://github.com/rehmanul/CAD-Analyzer-Pro-V-4
 ! [remote rejected] main -> main (failed)
error: failed to push some refs to 'https://github.com/rehmanul/CAD-Analyzer-Pro-V-4'
~/workspace$ 