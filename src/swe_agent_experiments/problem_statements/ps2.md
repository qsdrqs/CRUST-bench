You are provided with a Rust project that must pass all the tests defined in the src/bin folder. In case the code contains errors, you must repair the provided Rust files such that all test cases pass. 

You first run `cargo build` to determine what errors exist in the project. Incase you don't find any errors you try running tests defined in the project using `cargo test`. Incase you find any errors when executing `cargo build` and  `cargo test` you must address them by changing the Rust code in the src/ folder of the project. Incase you don't find any errors, you submit the project. 
You must ensure that you follow the following instructions:
  - You must not change the function signatures and return types of the functions when you are performing repair on a file.
  - You must address each error by carefully reasoning about it.
  - Each error must be solved using safe Rust code.
  - The transpiled Rust code must not contain Foreign Function Interface calls, such as the libc library.
  - All imports in the rust project must be in the following format - 
    ```rust
      use crate::file_name::module;
    ```
  - You must ensure that you include the required files and constants that are referenced in each Rust file.
  - You must ensure that you do not change the test code in the src/bin folder.
  - Warnings in the code are permissible.
  - Indentation fixes are not required.
Please think step-by-step and resolve the issue.


