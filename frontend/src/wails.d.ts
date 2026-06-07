declare global {
  interface Window {
    runtime?: {
      EventsOn(eventName: string, callback: (...data: unknown[]) => void): () => void;
      EventsOff(eventName: string, ...additionalEventNames: string[]): void;
    };
    go?: {
      main?: {
        App?: {
          LoadConfig(): Promise<AppConfig>;
          SaveConfig(config: AppConfig): Promise<void>;
          ScanDirectory(path: string, recursive: boolean): Promise<ScanResult>;
          PlanPrepare(scan: PrepareScanInput, outputDir: string, options: PrepareOptions): Promise<PrepareOperation[]>;
          ExecutePrepare(operations: PrepareOperation[], overwrite: boolean): Promise<PrepareResult>;
          PreviewAVIFCommand(inputPath: string, outputPath: string, params: AVIFParams, avifencPath: string): Promise<string[]>;
          CompressAVIF(inputPath: string, outputPath: string, params: AVIFParams, avifencPath: string): Promise<CompressResult>;
          CompressDirectory(options: CompressBatchOptions): Promise<CompressBatchResult>;
          BuildPreviewItems(result: CompressBatchResult, limit: number): Promise<PreviewItem[]>;
          ReadImageDataURL(path: string): Promise<string>;
          RunPrepareCompressUpload(options: RunAllOptions): Promise<RunAllResult>;
          UploadDirectory(inputDir: string, recursive: boolean, config: AppConfig['upload']): Promise<UploadResult>;
          UploadDirectoryWithRoot(inputDir: string, recursive: boolean, config: AppConfig['upload'], remoteRootDir: string): Promise<UploadResult>;
          CheckAVIFEnc(avifencPath: string): Promise<string>;
        };
      };
    };
  }
}

export type AppConfig = {
  last_input_dir: string;
  last_output_dir: string;
  avifenc_path: string;
  language: string;
  theme: string;
  prepare: {
    rename_images: boolean;
    rename_videos: boolean;
    strip_exif: boolean;
    output_mode: string;
  };
  compress: {
    format: string;
    avif: {
      min_quality: number;
      max_quality: number;
      speed: number;
      threads: string;
      yuv: string;
      depth: number;
      alpha_enabled: boolean;
      alpha_min: number;
      alpha_max: number;
      lossless: boolean;
      progressive: boolean;
    };
    webp_jpeg: {
      quality: number;
      lossless: boolean;
    };
    skip_videos: boolean;
    resize_mode: string;
    resize_value: number;
    keep_aspect_ratio: boolean;
    workers: number;
    conflict_strategy: string;
  };
  upload: {
    protocol: string;
    custom_path: string;
    s3: {
      endpoint: string;
      bucket: string;
      access_key: string;
      secret_key: string;
      region: string;
      prefix: string;
      domain: string;
    };
    ftp: {
      host: string;
      port: number;
      username: string;
      password: string;
      remote_dir: string;
      base_url: string;
    };
    sftp: {
      host: string;
      port: number;
      username: string;
      password: string;
      key_path: string;
      remote_dir: string;
      base_url: string;
      domain_root: string;
    };
    proxy: {
      enabled: boolean;
      url: string;
      type: string;
      host: string;
      port: number;
      username: string;
      password: string;
    };
  };
};

export type ScanResult = {
  baseDir: string;
  images: string[];
  videos: string[];
  others: string[];
  totalSize: number;
  subdirs: number;
};

export type PrepareScanInput = {
  BaseDir: string;
  Images: string[];
  Videos: string[];
};

export type PrepareOptions = {
  RenameImages: boolean;
  RenameVideos: boolean;
  Overwrite: boolean;
};

export type PrepareOperation = {
  source: string;
  destination: string;
  kind: string;
};

export type PrepareResult = {
  renamedImages: number;
  renamedVideos: number;
  totalFiles: number;
  outputDir: string;
};

export type AVIFParams = {
  Quality: number;
  Speed: number;
  Lossless: boolean;
  ResizeMode: string;
  ResizeValue: number;
  KeepAspectRatio: boolean;
  StripExif: boolean;
  KeepICC: boolean;
  StripXMP: boolean;
  Extra: Record<string, string | number | boolean>;
};

export type CompressResult = {
  success: boolean;
  inputPath: string;
  outputPath: string;
  originalSize: number;
  compressedSize: number;
  elapsedSeconds: number;
  error?: string;
};

export type CompressBatchOptions = {
  InputDir: string;
  OutputDir: string;
  Format: string;
  Recursive: boolean;
  Overwrite: boolean;
  ConflictStrategy: string;
  AVIFEncPath: string;
  CWebPPath: string;
  MaxWorkers: number;
  Params: AVIFParams;
};

export type CompressBatchResult = {
  totalFiles: number;
  compressedFiles: number;
  skippedFiles: number;
  failedFiles: number;
  outputDir: string;
  originalSize: number;
  compressedSize: number;
  elapsedSeconds: number;
  results: CompressResult[];
  errors: string[];
};

export type PreviewItem = {
  inputPath: string;
  outputPath: string;
  originalSize: number;
  compressedSize: number;
  savedPercent: number;
};

export type UploadResult = {
  totalFiles: number;
  uploadedFiles: number;
  failedFiles: number;
  urls: string[];
  errors: string[];
};

export type RunAllOptions = {
  prepareOperations: PrepareOperation[];
  prepareOverwrite: boolean;
  compressOptions: CompressBatchOptions;
  uploadConfig: AppConfig['upload'];
  uploadRecursive: boolean;
  uploadRootDir: string;
};

export type RunAllResult = {
  prepare: PrepareResult;
  compress: CompressBatchResult;
  upload: UploadResult;
};

export {};
