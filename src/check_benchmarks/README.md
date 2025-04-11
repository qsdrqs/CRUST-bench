The following folder does a sanity check over the interfaces and runs type checking between the `src/` files and `test` files.

Running `check_build.py` will create a Rust_formatted folder in the datasets directory and compile that, this shifts the files defined in `src/interfaces` to the `src` folder so that they can be compiled using the `cargo build` command.