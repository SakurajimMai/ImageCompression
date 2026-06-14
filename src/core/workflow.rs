use crate::config;
use crate::core::{compress, prepare, upload as up};

pub struct Options {
    pub prepare_ops: Vec<prepare::Operation>,
    pub prepare_overwrite: bool,
    pub compress_opts: compress::BatchOptions,
    pub upload_cfg: Option<config::UploadConfig>,
    pub do_upload: bool,
}

pub struct WorkflowResult {
    pub prepare: prepare::PrepareResult,
    pub compress: compress::BatchResult,
    pub upload: Option<up::UploadResult>,
}

pub fn run_prepare_compress_upload(opts: Options) -> anyhow::Result<WorkflowResult> {
    let prep = prepare::execute_operations(opts.prepare_ops, opts.prepare_overwrite, None)?;

    let mut comp_opts = opts.compress_opts;
    comp_opts.input_dir = prep.output_dir.clone();

    let comp = compress::compress_directory(std::sync::Arc::new(()), comp_opts, None, None)?;

    let up_res = if opts.do_upload {
        if let Some(uc) = opts.upload_cfg {
            let eff = up::effective_config(uc, &comp.output_dir);
            let mut u = crate::core::upload::build_uploader(eff);
            Some(up::upload_directory(
                &mut *u,
                &comp.output_dir,
                up::Options { recursive: true },
                None,
            )?)
        } else {
            None
        }
    } else {
        None
    };

    Ok(WorkflowResult {
        prepare: prep,
        compress: comp,
        upload: up_res,
    })
}
