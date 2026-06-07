import React, { Component, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive,
  CloudUpload,
  Copy,
  FileSearch,
  Gauge,
  HelpCircle,
  ImageIcon,
  Play,
  RefreshCw,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import type {
  AppConfig,
  AVIFParams,
  CompressBatchResult,
  PrepareOperation,
  PrepareOptions,
  PrepareScanInput,
  PreviewItem,
  ScanResult,
  UploadResult,
} from './wails';
import './styles.css';

type TabKey = 'prepare' | 'compress' | 'upload' | 'settings' | 'help';

type PreviewImages = {
  original: string;
  compressed: string;
  item: PreviewItem;
} | null;

const fallbackConfig: AppConfig = {
  last_input_dir: '',
  last_output_dir: '',
  avifenc_path: '',
  language: 'zh',
  theme: 'light',
  prepare: {
    rename_images: true,
    rename_videos: true,
    strip_exif: true,
    output_mode: 'new_directory',
  },
  compress: {
    format: 'avif',
    avif: {
      min_quality: 20,
      max_quality: 40,
      speed: 6,
      threads: 'all',
      yuv: '420',
      depth: 8,
      alpha_enabled: false,
      alpha_min: 20,
      alpha_max: 40,
      lossless: false,
      progressive: false,
    },
    webp_jpeg: {
      quality: 80,
      lossless: false,
    },
    skip_videos: true,
    resize_mode: 'none',
    resize_value: 0,
    keep_aspect_ratio: true,
    workers: 1,
    conflict_strategy: 'rename',
  },
  upload: {
    protocol: 's3',
    custom_path: '',
    s3: {
      endpoint: '',
      bucket: '',
      access_key: '',
      secret_key: '',
      region: '',
      prefix: '',
      domain: '',
    },
    ftp: {
      host: '',
      port: 21,
      username: '',
      password: '',
      remote_dir: '/',
      base_url: '',
    },
    sftp: {
      host: '',
      port: 22,
      username: '',
      password: '',
      key_path: '',
      remote_dir: '/',
      base_url: '',
      domain_root: '',
    },
    proxy: {
      enabled: false,
      url: 'socks5://127.0.0.1:7890',
      type: 'socks5',
      host: '127.0.0.1',
      port: 7890,
      username: '',
      password: '',
    },
  },
};

function backend() {
  return window.go?.main?.App;
}

function runtimeEventsOn(eventName: string, callback: (...data: unknown[]) => void) {
  return window.runtime?.EventsOn?.(eventName, callback) ?? (() => {});
}

function runtimeEventsOff(eventName: string) {
  window.runtime?.EventsOff?.(eventName);
}

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('prepare');
  const [config, setConfig] = useState<AppConfig>(fallbackConfig);
  const [inputDir, setInputDir] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [preparePlan, setPreparePlan] = useState<PrepareOperation[]>([]);
  const [avifCommand, setAvifCommand] = useState<string[]>([]);
  const [compressResult, setCompressResult] = useState<CompressBatchResult | null>(null);
  const [previewItems, setPreviewItems] = useState<PreviewItem[]>([]);
  const [previewImages, setPreviewImages] = useState<PreviewImages>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadRootDir, setUploadRootDir] = useState('');
  const [status, setStatus] = useState('Go/Wails 版本已作为当前主版本运行。');
  const configReady = useRef(false);
  const uploadCancelRef = useRef<(() => void) | null>(null);
  const compressCancelRef = useRef<(() => void) | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressProgress, setCompressProgress] = useState<CompressProgressEvent | null>(null);

  useEffect(() => {
    const api = backend();
    if (!api) {
      setStatus('浏览器预览模式：未连接 Wails 后端，界面使用本地示例状态。');
      return;
    }
    api.LoadConfig()
      .then((loaded) => {
        setConfig(loaded);
        setInputDir(loaded.last_input_dir ?? '');
        setOutputDir(loaded.last_output_dir ?? '');
        // Allow the auto-save effect to take over after the first load.
        queueMicrotask(() => {
          configReady.current = true;
        });
      })
      .catch((error) => {
        setStatus(`配置加载失败：${String(error)}`);
        configReady.current = true;
      });
  }, []);

  // Auto-persist any change to config / input dir / output dir so that
  // closing the app (without going to the Settings tab) does not lose state.
  useEffect(() => {
    if (!configReady.current) {
      return;
    }
    const api = backend();
    if (!api) {
      return;
    }
    const timer = setTimeout(() => {
      const nextConfig = {
        ...config,
        last_input_dir: inputDir,
        last_output_dir: outputDir,
      };
      api
        .SaveConfig(nextConfig)
        .catch((error) => setStatus(`自动保存失败：${String(error)}`));
    }, 300);
    return () => clearTimeout(timer);
  }, [config, inputDir, outputDir]);

  // Drop any pending upload event subscription when the component unmounts.
  useEffect(() => {
    return () => {
      if (uploadCancelRef.current) {
        uploadCancelRef.current();
        uploadCancelRef.current = null;
      }
    };
  }, []);

  // Subscribe to compress progress events from the Go backend.
  useEffect(() => {
    const off = runtimeEventsOn('compress', (raw) => {
      if (typeof raw !== 'string') return;
      const event = parseCompressEvent(raw);
      if (!event) return;
      setCompressProgress(event);
      if (event.done) {
        setIsCompressing(false);
      } else if (event.start) {
        setIsCompressing(true);
      }
    });
    return () => {
      off();
      runtimeEventsOff('compress');
    };
  }, []);

  const stats = useMemo(() => {
    if (!scan) {
      return [
        ['图片', '-'],
        ['视频', '-'],
        ['其他', '-'],
        ['体积', '-'],
      ];
    }
    return [
      ['图片', String(scan.images.length)],
      ['视频', String(scan.videos.length)],
      ['其他', String(scan.others.length)],
      ['体积', formatSize(scan.totalSize)],
    ];
  }, [scan]);

  function handleInputDirChange(value: string) {
    setInputDir(value);
    setUploadRootDir('');
  }

  async function runScan() {
    if (!inputDir.trim()) {
      setStatus('请先输入要扫描的目录。');
      return;
    }
    const api = backend();
    if (!api) {
      const demo: ScanResult = {
        baseDir: inputDir,
        images: [`${inputDir}/0001.png`, `${inputDir}/0002.jpg`],
        videos: [`${inputDir}/clip.mp4`],
        others: [],
        totalSize: 1024 * 1024 * 14,
        subdirs: 1,
      };
      setScan(demo);
      setUploadRootDir(demo.baseDir);
      setStatus('浏览器预览模式：已生成示例扫描结果。');
      return;
    }
    try {
      const result = normalizeScanResult(await api.ScanDirectory(inputDir, recursive));
      setScan(result);
      setUploadRootDir(result.baseDir);
      setStatus(`扫描完成：${result.images.length} 张图片，${result.videos.length} 个视频。`);
    } catch (error) {
      setStatus(`扫描失败：${String(error)}`);
    }
  }

  async function buildPreparePlan() {
    if (!scan) {
      setStatus('请先扫描目录。');
      return;
    }
    const targetDir = outputDir || `${scan.baseDir}_prepared`;
    const payload: PrepareScanInput = {
      BaseDir: scan.baseDir,
      Images: scan.images,
      Videos: scan.videos,
    };
    const options: PrepareOptions = {
      RenameImages: config.prepare.rename_images,
      RenameVideos: config.prepare.rename_videos,
      Overwrite: config.prepare.output_mode === 'overwrite',
    };
    const api = backend();
    try {
      const plan = api
        ? await api.PlanPrepare(payload, targetDir, options)
        : scan.images.map((source: string, index: number) => ({
            source,
            destination: `${targetDir}/${String(index + 1).padStart(4, '0')}.png`,
            kind: 'image',
          }));
      setPreparePlan(plan);
      setStatus(`准备计划已生成：${plan.length} 个文件操作。`);
    } catch (error) {
      setStatus(`准备计划生成失败：${String(error)}`);
    }
  }

  async function executePrepare() {
    if (!scan && !preparePlan.length) {
      setStatus('请先扫描目录。');
      return;
    }
    const api = backend();
    if (!api) {
      setStatus('浏览器预览模式：无法执行文件复制。');
      return;
    }
    try {
      let plan = preparePlan;
      if (!plan.length && scan) {
        const targetDir = outputDir || `${scan.baseDir}_prepared`;
        plan = await api.PlanPrepare(
          { BaseDir: scan.baseDir, Images: scan.images, Videos: scan.videos },
          targetDir,
          {
            RenameImages: config.prepare.rename_images,
            RenameVideos: config.prepare.rename_videos,
            Overwrite: config.prepare.output_mode === 'overwrite',
          },
        );
        setPreparePlan(plan);
      }
      const result = await api.ExecutePrepare(plan, config.prepare.output_mode === 'overwrite');
      setUploadRootDir(uploadRootDir || scan?.baseDir || result.outputDir);
      setInputDir(result.outputDir);
      setOutputDir('');
      setStatus(`准备完成：${result.totalFiles} 个文件，输出目录 ${result.outputDir}`);
    } catch (error) {
      setStatus(`准备执行失败：${String(error)}`);
    }
  }

  async function executePrepareAndCompress() {
    if (!scan) {
      setStatus('请先扫描目录。');
      return;
    }
    const api = backend();
    if (!api) {
      setStatus('浏览器预览模式：无法执行准备和压缩链路。');
      return;
    }
    const targetDir = outputDir || `${scan.baseDir}_prepared`;
    try {
      const plan = preparePlan.length
        ? preparePlan
        : await api.PlanPrepare(
            { BaseDir: scan.baseDir, Images: scan.images, Videos: scan.videos },
            targetDir,
            {
              RenameImages: config.prepare.rename_images,
              RenameVideos: config.prepare.rename_videos,
              Overwrite: config.prepare.output_mode === 'overwrite',
            },
          );
      setPreparePlan(plan);
      const prepared = await api.ExecutePrepare(plan, config.prepare.output_mode === 'overwrite');
      const compressOutput = `${prepared.outputDir}_compressed`;
      const result = await api.CompressDirectory({
        InputDir: prepared.outputDir,
        OutputDir: compressOutput,
        Format: config.compress.format,
        Recursive: recursive,
        Overwrite: false,
        ConflictStrategy: config.compress.conflict_strategy || 'rename',
        AVIFEncPath: config.avifenc_path,
        CWebPPath: 'cwebp',
        MaxWorkers: config.compress.workers,
        Params: buildCompressParams(config),
      });
      const normalized = normalizeCompressBatchResult(result);
      setCompressResult(normalized);
      setPreviewItems(await api.BuildPreviewItems(normalized, 4));
      setUploadRootDir(scan.baseDir);
      setInputDir(normalized.outputDir);
      setOutputDir('');
      setActiveTab('upload');
      setStatus(`准备并压缩完成：${normalized.compressedFiles}/${normalized.totalFiles} 个文件成功，可继续上传。`);
    } catch (error) {
      setStatus(`准备并压缩失败：${String(error)}`);
    }
  }

  async function executeFullWorkflow() {
    if (!scan) {
      setStatus('请先扫描目录。');
      return;
    }
    const api = backend();
    if (!api) {
      setStatus('浏览器预览模式：无法执行真实上传链路。');
      return;
    }
    const targetDir = outputDir || `${scan.baseDir}_prepared`;
    try {
      const plan = preparePlan.length
        ? preparePlan
        : await api.PlanPrepare(
            { BaseDir: scan.baseDir, Images: scan.images, Videos: scan.videos },
            targetDir,
            {
              RenameImages: config.prepare.rename_images,
              RenameVideos: config.prepare.rename_videos,
              Overwrite: config.prepare.output_mode === 'overwrite',
            },
          );
      setPreparePlan(plan);
      const result = await api.RunPrepareCompressUpload({
        prepareOperations: plan,
        prepareOverwrite: config.prepare.output_mode === 'overwrite',
        compressOptions: {
          InputDir: targetDir,
          OutputDir: `${targetDir}_compressed`,
          Format: config.compress.format,
          Recursive: recursive,
          Overwrite: false,
          ConflictStrategy: config.compress.conflict_strategy || 'rename',
          AVIFEncPath: config.avifenc_path,
          CWebPPath: 'cwebp',
          MaxWorkers: config.compress.workers,
          Params: buildCompressParams(config),
        },
        uploadConfig: config.upload,
        uploadRecursive: recursive,
        uploadRootDir: scan.baseDir,
      });
      const compressResult = normalizeCompressBatchResult(result.compress);
      const uploadResult = normalizeUploadResult(result.upload);
      setCompressResult(compressResult);
      setPreviewItems(await api.BuildPreviewItems(compressResult, 4));
      setUploadResult(uploadResult);
      setUploadRootDir(scan.baseDir);
      setInputDir(compressResult.outputDir);
      setOutputDir('');
      setActiveTab('upload');
      setStatus(`全流程完成：压缩 ${compressResult.compressedFiles}/${compressResult.totalFiles}，上传 ${uploadResult.uploadedFiles}/${uploadResult.totalFiles}。`);
    } catch (error) {
      setStatus(`全流程执行失败：${String(error)}`);
    }
  }

  async function previewCommand() {
    const params = buildAVIFParams(config);
    const api = backend();
    const input = scan?.images[0] ?? 'input.png';
    const output = outputDir ? `${outputDir}/output.avif` : 'output.avif';
    try {
      const command = api
        ? await api.PreviewAVIFCommand(input, output, params, config.avifenc_path)
        : ['avifenc', '--min', '20', '--max', '40', input, output];
      setAvifCommand(command);
      setStatus('已生成 AVIF 命令预览。');
    } catch (error) {
      setStatus(`命令预览失败：${String(error)}`);
    }
  }

  async function compressFirstImage() {
    if (!scan?.images.length) {
      setStatus('请先扫描至少一张图片。');
      return;
    }
    const api = backend();
    if (!api) {
      setStatus('浏览器预览模式：无法执行 avifenc。');
      return;
    }
    const input = scan.images[0];
    const output = outputDir ? `${outputDir}/wails-preview.avif` : `${input}.avif`;
    try {
      const result = await api.CompressAVIF(input, output, buildAVIFParams(config), config.avifenc_path);
      setStatus(result.success ? `压缩完成：${formatSize(result.originalSize)} -> ${formatSize(result.compressedSize)}` : `压缩失败：${result.error ?? '未知错误'}`);
    } catch (error) {
      setStatus(`压缩执行失败：${String(error)}`);
    }
  }

  async function executeCompressDirectory() {
    if (!inputDir.trim()) {
      setStatus('请先输入要压缩的目录。');
      return;
    }
    const api = backend();
    if (!api) {
      setCompressResult({
        totalFiles: 2,
        compressedFiles: 2,
        skippedFiles: 0,
        failedFiles: 0,
        outputDir: outputDir || `${inputDir}_compressed`,
        originalSize: 1024 * 1024 * 6,
        compressedSize: 1024 * 1024 * 2,
        elapsedSeconds: 1.2,
        results: [],
        errors: [],
      });
      setPreviewItems([
        {
          inputPath: `${inputDir}/0001.png`,
          outputPath: `${outputDir || `${inputDir}_compressed`}/0001.avif`,
          originalSize: 1024 * 1024 * 4,
          compressedSize: 1024 * 1024,
          savedPercent: 75,
        },
      ]);
      setStatus('浏览器预览模式：已生成示例批量压缩结果。');
      return;
    }
    try {
      setIsCompressing(true);
      setCompressProgress({
        current: 0,
        total: 0,
        currentFile: '',
        message: '准备压缩...',
        compressed: 0,
        skipped: 0,
        failed: 0,
        original: 0,
        compressedSize: 0,
        speed: 0,
        elapsedSec: 0,
        start: true,
      });
      const result = await api.CompressDirectory({
        InputDir: inputDir,
        OutputDir: outputDir || `${inputDir}_compressed`,
        Format: config.compress.format,
        Recursive: recursive,
        Overwrite: config.prepare.output_mode === 'overwrite',
        ConflictStrategy: config.prepare.output_mode === 'overwrite' ? 'overwrite' : config.compress.conflict_strategy,
        AVIFEncPath: config.avifenc_path,
        CWebPPath: 'cwebp',
        MaxWorkers: config.compress.workers,
        Params: buildCompressParams(config),
      });
      const normalized = normalizeCompressBatchResult(result);
      setCompressResult(normalized);
      setPreviewItems(await api.BuildPreviewItems(normalized, 4));
      setInputDir(normalized.outputDir);
      setOutputDir('');
      setUploadRootDir(uploadRootDir || inputDir);
      setIsCompressing(false);
      setStatus(`批量压缩完成：${result.compressedFiles}/${result.totalFiles} 个文件成功。`);
    } catch (error) {
      setIsCompressing(false);
      setStatus(`批量压缩失败：${String(error)}`);
    }
  }

  function clearCompress() {
    setCompressResult(null);
    setPreviewItems([]);
    setPreviewImages(null);
    setCompressProgress(null);
  }

  function clearUpload() {
    setUploadResult(null);
  }

  async function openPreviewItem(item: PreviewItem) {
    const api = backend();
    if (!api) {
      setPreviewImages({
        item,
        original: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420"><rect width="100%" height="100%" fill="%23e2e8f0"/><text x="50%" y="50%" text-anchor="middle" fill="%23334155" font-family="Segoe UI" font-size="28">Original Preview</text></svg>',
        compressed: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420"><rect width="100%" height="100%" fill="%23dcfce7"/><text x="50%" y="50%" text-anchor="middle" fill="%23047857" font-family="Segoe UI" font-size="28">Compressed Preview</text></svg>',
      });
      setStatus('浏览器预览模式：已加载示例图片预览。');
      return;
    }
    try {
      const [original, compressed] = await Promise.all([
        api.ReadImageDataURL(item.inputPath),
        api.ReadImageDataURL(item.outputPath),
      ]);
      setPreviewImages({ item, original, compressed });
      setStatus(`已加载预览：${basename(item.inputPath)}`);
    } catch (error) {
      setStatus(`图片预览加载失败：${String(error)}`);
    }
  }

  async function executeUpload() {
    if (!inputDir.trim()) {
      setStatus('请先输入要上传的目录。');
      return;
    }
    const api = backend();
    if (!api) {
      setUploadResult({
        totalFiles: 2,
        uploadedFiles: 2,
        failedFiles: 0,
        urls: ['https://cdn.example.com/a.avif', 'https://cdn.example.com/sub/b.webp'],
        errors: [],
      });
      setStatus('浏览器预览模式：已生成示例上传结果。');
      return;
    }
    // Tear down any previous subscription before starting a new upload so
    // overlapping events from a stale run cannot pollute the new result.
    if (uploadCancelRef.current) {
      uploadCancelRef.current();
      uploadCancelRef.current = null;
    }
    setIsUploading(true);
    setUploadResult({ totalFiles: 0, uploadedFiles: 0, failedFiles: 0, urls: [], errors: [] });
    setStatus('正在准备上传...');

    let lastStart = 0;
    const offStart = runtimeEventsOn('upload', (raw) => {
      if (typeof raw !== 'string') return;
      const event = parseUploadEvent(raw);
      if (!event) return;
      if (event.start) {
        lastStart = event.total;
        setUploadResult({
          totalFiles: event.total,
          uploadedFiles: 0,
          failedFiles: 0,
          urls: [],
          errors: [],
        });
        setStatus(`开始上传 ${event.total} 个文件`);
      } else if (event.done) {
        setUploadResult((prev) => ({
          totalFiles: event.total || prev?.totalFiles || 0,
          uploadedFiles: event.uploaded,
          failedFiles: event.failed,
          urls: prev?.urls ?? [],
          errors: prev?.errors ?? [],
        }));
        if (event.error) {
          setStatus(`上传中断：${event.error}`);
        } else {
          setStatus(`上传完成：${event.uploaded} 成功 / ${event.failed} 失败（总计 ${event.total}）`);
        }
        setIsUploading(false);
      } else {
        setUploadResult((prev) => {
          const urls = prev?.urls ?? [];
          const errors = prev?.errors ?? [];
          return {
            totalFiles: event.total || prev?.totalFiles || lastStart,
            uploadedFiles: event.uploaded,
            failedFiles: event.failed,
            urls: event.url ? [...urls, event.url] : urls,
            errors: event.error ? [...errors, `${event.message}: ${event.error}`] : errors,
          };
        });
        setStatus(`${event.current}/${event.total || lastStart}  ${event.message}`);
      }
    });
    uploadCancelRef.current = () => {
      offStart();
      runtimeEventsOff('upload');
    };

    try {
      const result = await api.UploadDirectoryWithRoot(inputDir, recursive, config.upload, uploadRootDir || inputDir);
      // Streamed events already updated the result; final reconcile covers
      // the case where the backend short-circuited without any per-file events.
      setUploadResult((prev) => ({
        totalFiles: result.totalFiles || prev?.totalFiles || 0,
        uploadedFiles: result.uploadedFiles,
        failedFiles: result.failedFiles,
        urls: result.urls.length ? result.urls : prev?.urls ?? [],
        errors: result.errors.length ? result.errors : prev?.errors ?? [],
      }));
    } catch (error) {
      setStatus(`上传执行失败：${String(error)}`);
      setIsUploading(false);
    }
  }

  async function saveSettings() {
    // 配置已在 useEffect 中自动持久化，这里只做一次"立即落盘"并提示用户。
    const api = backend();
    const nextConfig = {
      ...config,
      last_input_dir: inputDir,
      last_output_dir: outputDir,
    };
    if (!api) {
      setStatus('浏览器预览模式：未连接 Wails 后端，无法写入配置文件。');
      return;
    }
    try {
      await api.SaveConfig(nextConfig);
      setStatus('设置已保存。');
    } catch (error) {
      setStatus(`设置保存失败：${String(error)}`);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <ImageIcon size={22} />
          </div>
          <div>
            <strong>Image Compression</strong>
            <span>Go Workbench</span>
          </div>
        </div>
        <nav>
          <NavButton icon={<FileSearch size={18} />} label="准备" active={activeTab === 'prepare'} onClick={() => setActiveTab('prepare')} />
          <NavButton icon={<Archive size={18} />} label="压缩" active={activeTab === 'compress'} onClick={() => setActiveTab('compress')} />
          <NavButton icon={<CloudUpload size={18} />} label="上传" active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} />
          <NavButton icon={<Settings size={18} />} label="设置" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <NavButton icon={<HelpCircle size={18} />} label="说明" active={activeTab === 'help'} onClick={() => setActiveTab('help')} />
        </nav>
        <div className="status-panel">
          <ShieldCheck size={18} />
          <p>{status}</p>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Go desktop</span>
            <h1>{tabTitle(activeTab)}</h1>
          </div>
          <button className="ghost-button" onClick={runScan}>
            <RefreshCw size={16} />
            扫描
          </button>
        </header>

        {activeTab === 'prepare' && (
          <PrepareView
            inputDir={inputDir}
            setInputDir={handleInputDirChange}
            outputDir={outputDir}
            setOutputDir={setOutputDir}
            recursive={recursive}
            setRecursive={setRecursive}
            config={config}
            setConfig={setConfig}
            stats={stats}
            preparePlan={preparePlan}
            onScan={runScan}
            onPlan={buildPreparePlan}
            onExecute={executePrepare}
            onExecuteAndCompress={executePrepareAndCompress}
            onExecuteFullWorkflow={executeFullWorkflow}
          />
        )}
        {activeTab === 'compress' && (
          <CompressView
            config={config}
            setConfig={setConfig}
            inputDir={inputDir}
            setInputDir={handleInputDirChange}
            outputDir={outputDir}
            setOutputDir={setOutputDir}
            recursive={recursive}
            setRecursive={setRecursive}
            avifCommand={avifCommand}
            compressResult={compressResult}
            previewItems={previewItems}
            previewImages={previewImages}
            isCompressing={isCompressing}
            compressProgress={compressProgress}
            onPreviewCommand={previewCommand}
            onCompressFirstImage={compressFirstImage}
            onCompressDirectory={executeCompressDirectory}
            onOpenPreviewItem={openPreviewItem}
            onClear={clearCompress}
          />
        )}
        {activeTab === 'upload' && (
          <UploadView
            config={config}
            setConfig={setConfig}
            inputDir={inputDir}
            setInputDir={handleInputDirChange}
            recursive={recursive}
            setRecursive={setRecursive}
            uploadResult={uploadResult}
            isUploading={isUploading}
            onUpload={executeUpload}
            onClear={clearUpload}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsView
            config={config}
            setConfig={setConfig}
            inputDir={inputDir}
            outputDir={outputDir}
            saveSettings={saveSettings}
          />
        )}
        {activeTab === 'help' && <HelpView />}
      </section>
    </main>
  );
}

function NavButton(props: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button className={props.active ? 'nav-button active' : 'nav-button'} onClick={props.onClick}>
      {props.icon}
      {props.label}
    </button>
  );
}

function PrepareView(props: {
  inputDir: string;
  setInputDir: (value: string) => void;
  outputDir: string;
  setOutputDir: (value: string) => void;
  recursive: boolean;
  setRecursive: (value: boolean) => void;
  config: AppConfig;
  setConfig: (value: AppConfig) => void;
  stats: string[][];
  preparePlan: PrepareOperation[];
  onScan: () => void;
  onPlan: () => void;
  onExecute: () => void;
  onExecuteAndCompress: () => void;
  onExecuteFullWorkflow: () => void;
}) {
  return (
    <div className="content-grid">
      <section className="panel wide">
        <h2>目录输入</h2>
        <Field label="输入目录" value={props.inputDir} onChange={props.setInputDir} placeholder="D:/photos/raw" />
        <Field label="输出目录" value={props.outputDir} onChange={props.setOutputDir} placeholder="D:/photos/prepared" />
        <label className="switch-row">
          <input type="checkbox" checked={props.recursive} onChange={(event) => props.setRecursive(event.target.checked)} />
          <span>递归扫描子目录</span>
        </label>
        <div className="button-row">
          <button onClick={props.onScan}>
            <FileSearch size={16} />
            扫描目录
          </button>
          <button onClick={props.onPlan}>
            <Play size={16} />
            生成准备计划
          </button>
          <button onClick={props.onExecute}>
            <Archive size={16} />
            执行准备
          </button>
          <button onClick={props.onExecuteAndCompress}>
            <Play size={16} />
            准备并压缩
          </button>
          <button onClick={props.onExecuteFullWorkflow}>
            <CloudUpload size={16} />
            准备压缩上传
          </button>
        </div>
      </section>
      <section className="panel">
        <h2>扫描概览</h2>
        <div className="metric-grid">
          {props.stats.map(([label, value]) => (
            <div className="metric" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>准备选项</h2>
        <Checkbox
          label="重命名图片"
          checked={props.config.prepare.rename_images}
          onChange={(checked) => props.setConfig({ ...props.config, prepare: { ...props.config.prepare, rename_images: checked } })}
        />
        <Checkbox
          label="重命名视频"
          checked={props.config.prepare.rename_videos}
          onChange={(checked) => props.setConfig({ ...props.config, prepare: { ...props.config.prepare, rename_videos: checked } })}
        />
        <Checkbox
          label="清除 EXIF"
          checked={props.config.prepare.strip_exif}
          onChange={(checked) => props.setConfig({ ...props.config, prepare: { ...props.config.prepare, strip_exif: checked } })}
        />
      </section>
      <section className="panel wide">
        <h2>准备计划</h2>
        <OperationList operations={props.preparePlan} />
      </section>
    </div>
  );
}

function CompressView(props: {
  config: AppConfig;
  setConfig: (value: AppConfig) => void;
  inputDir: string;
  setInputDir: (value: string) => void;
  outputDir: string;
  setOutputDir: (value: string) => void;
  recursive: boolean;
  setRecursive: (value: boolean) => void;
  avifCommand: string[];
  compressResult: CompressBatchResult | null;
  previewItems: PreviewItem[];
  previewImages: PreviewImages;
  isCompressing: boolean;
  compressProgress: CompressProgressEvent | null;
  onPreviewCommand: () => void;
  onCompressFirstImage: () => void;
  onCompressDirectory: () => void;
  onOpenPreviewItem: (item: PreviewItem) => void;
  onClear: () => void;
}) {
  const compress = props.config.compress;
  const avif = compress.avif;
  const webpJpeg = compress.webp_jpeg;
  const setCompress = (value: AppConfig['compress']) => props.setConfig({ ...props.config, compress: value });
  const setAvif = <K extends keyof AppConfig['compress']['avif']>(key: K, value: AppConfig['compress']['avif'][K]) => {
    setCompress({ ...compress, avif: { ...avif, [key]: value } });
  };
  const setWebPJpeg = <K extends keyof AppConfig['compress']['webp_jpeg']>(key: K, value: AppConfig['compress']['webp_jpeg'][K]) => {
    setCompress({ ...compress, webp_jpeg: { ...webpJpeg, [key]: value } });
  };

  return (
    <div className="content-grid">
      <section className="panel wide">
        <h2>压缩目录</h2>
        <div className="form-grid">
          <Field label="输入目录" value={props.inputDir} onChange={props.setInputDir} placeholder="D:/photos/prepared" />
          <Field label="输出目录" value={props.outputDir} onChange={props.setOutputDir} placeholder="留空自动生成 _compressed 目录" />
        </div>
        <Checkbox label="递归压缩子目录" checked={props.recursive} onChange={props.setRecursive} />
        <div className="button-row">
          <button onClick={props.onCompressDirectory} disabled={props.isCompressing}>
            <Archive size={16} />
            {props.isCompressing ? '压缩中…' : '压缩目录'}
          </button>
        </div>
      </section>
      <section className="panel wide">
        <CompressProgressPanel progress={props.compressProgress} isCompressing={props.isCompressing} />
      </section>
      <section className="panel">
        <h2>格式</h2>
        <div className="segmented">
          {['avif', 'webp', 'jpeg'].map((format) => (
            <button
              key={format}
              className={compress.format === format ? 'selected' : ''}
              onClick={() => setCompress({ ...compress, format })}
            >
              {format.toUpperCase()}
            </button>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>AVIF 参数</h2>
        <div className="form-grid">
          <NumberField label="质量下限" value={avif.min_quality} min={0} max={63} onChange={(value) => setAvif('min_quality', value)} />
          <NumberField label="质量上限" value={avif.max_quality} min={0} max={63} onChange={(value) => setAvif('max_quality', value)} />
          <NumberField label="速度" value={avif.speed} min={0} max={10} onChange={(value) => setAvif('speed', value)} />
          <Field label="线程" value={avif.threads} onChange={(value) => setAvif('threads', value)} placeholder="all / 1 / 2 / 4" />
          <SelectField
            label="YUV"
            value={avif.yuv}
            onChange={(value) => setAvif('yuv', value)}
            options={[
              ['420', '420'],
              ['422', '422'],
              ['444', '444'],
            ]}
          />
          <SelectField
            label="位深"
            value={String(avif.depth)}
            onChange={(value) => setAvif('depth', Number(value))}
            options={[
              ['8', '8 bit'],
              ['10', '10 bit'],
              ['12', '12 bit'],
            ]}
          />
        </div>
        <Checkbox label="无损压缩" checked={avif.lossless} onChange={(checked) => setAvif('lossless', checked)} />
        <Checkbox label="渐进式输出" checked={avif.progressive} onChange={(checked) => setAvif('progressive', checked)} />
        <Checkbox label="Alpha 独立质量" checked={avif.alpha_enabled} onChange={(checked) => setAvif('alpha_enabled', checked)} />
        {avif.alpha_enabled && (
          <div className="form-grid">
            <NumberField label="Alpha 下限" value={avif.alpha_min} min={0} max={63} onChange={(value) => setAvif('alpha_min', value)} />
            <NumberField label="Alpha 上限" value={avif.alpha_max} min={0} max={63} onChange={(value) => setAvif('alpha_max', value)} />
          </div>
        )}
      </section>
      <section className="panel">
        <h2>WebP / JPEG</h2>
        <NumberField
          label="质量"
          value={webpJpeg.quality}
          min={1}
          max={100}
          onChange={(value) => setWebPJpeg('quality', value)}
        />
        <Checkbox label="WebP 无损压缩" checked={webpJpeg.lossless} onChange={(checked) => setWebPJpeg('lossless', checked)} />
      </section>
      <section className="panel">
        <h2>缩放</h2>
        <SelectField
          label="模式"
          value={compress.resize_mode}
          onChange={(value) => setCompress({ ...compress, resize_mode: value })}
          options={[
            ['none', '不缩放'],
            ['width', '按宽度'],
            ['height', '按高度'],
            ['percent', '按比例(%)'],
            ['long_edge', '长边限制'],
            ['short_edge', '短边限制'],
            ['fit', '适应框内'],
            ['fill', '填充裁剪'],
            ['exact', '强制拉伸'],
          ]}
        />
        <NumberField
          label={compress.resize_mode === 'percent' ? '比例' : '目标值'}
          value={compress.resize_value}
          min={compress.resize_mode === 'none' ? 0 : 1}
          max={compress.resize_mode === 'percent' ? 500 : 99999}
          onChange={(value) => setCompress({ ...compress, resize_value: value })}
        />
        <Checkbox
          label="保持纵横比"
          checked={compress.keep_aspect_ratio}
          onChange={(checked) => setCompress({ ...compress, keep_aspect_ratio: checked })}
        />
      </section>
      <section className="panel">
        <h2>批处理</h2>
        <NumberField label="并行数" value={compress.workers} min={1} max={32} onChange={(value) => setCompress({ ...compress, workers: value })} />
        <SelectField
          label="同名文件"
          value={compress.conflict_strategy}
          onChange={(value) => setCompress({ ...compress, conflict_strategy: value })}
          options={[
            ['rename', '重命名'],
            ['overwrite', '覆盖'],
            ['skip', '跳过'],
          ]}
        />
      </section>
      <section className="panel wide">
        <h2>命令预览</h2>
        <div className="button-row">
          <button onClick={props.onPreviewCommand}>
            <Gauge size={16} />
            生成 avifenc 命令
          </button>
          <button onClick={props.onCompressFirstImage}>
            <Play size={16} />
            压缩首张图片
          </button>
        </div>
        <pre className="command-preview">{props.avifCommand.length ? props.avifCommand.join(' ') : '等待生成命令...'}</pre>
      </section>
      <section className="panel wide">
        <h2>批量结果</h2>
        <CompressResultPanel
          result={props.compressResult}
          previewItems={props.previewItems}
          previewImages={props.previewImages}
          onOpenPreviewItem={props.onOpenPreviewItem}
          onClear={props.onClear}
        />
      </section>
    </div>
  );
}

function UploadView(props: {
  config: AppConfig;
  setConfig: (value: AppConfig) => void;
  inputDir: string;
  setInputDir: (value: string) => void;
  recursive: boolean;
  setRecursive: (value: boolean) => void;
  uploadResult: UploadResult | null;
  isUploading: boolean;
  onUpload: () => void;
  onClear: () => void;
}) {
  const upload = props.config.upload;
  const setUpload = (value: AppConfig['upload']) => props.setConfig({ ...props.config, upload: value });
  const setS3 = <K extends keyof AppConfig['upload']['s3']>(key: K, value: AppConfig['upload']['s3'][K]) => {
    setUpload({ ...upload, s3: { ...upload.s3, [key]: value } });
  };
  const setFTP = <K extends keyof AppConfig['upload']['ftp']>(key: K, value: AppConfig['upload']['ftp'][K]) => {
    setUpload({ ...upload, ftp: { ...upload.ftp, [key]: value } });
  };
  const setSFTP = <K extends keyof AppConfig['upload']['sftp']>(key: K, value: AppConfig['upload']['sftp'][K]) => {
    setUpload({ ...upload, sftp: { ...upload.sftp, [key]: value } });
  };

  return (
    <div className="content-grid">
      <section className="panel wide">
        <h2>上传目录</h2>
        <Field label="输入目录" value={props.inputDir} onChange={props.setInputDir} placeholder="D:/photos/output" />
        <Field
          label="自定义远程子路径"
          value={upload.custom_path}
          onChange={(value) => setUpload({ ...upload, custom_path: value })}
          placeholder="例如 photos/2026/spring"
        />
        <p className="hint">留空时使用源目录名作为子路径；填写后会拼接到协议根路径（如 S3 Prefix / FTP RemoteDir）后面。</p>
        <Checkbox label="递归上传子目录" checked={props.recursive} onChange={props.setRecursive} />
        <div className="button-row">
          <button onClick={props.onUpload} disabled={props.isUploading}>
            <CloudUpload size={16} />
            {props.isUploading ? '上传中…' : '开始上传'}
          </button>
        </div>
      </section>
      <section className="panel">
        <h2>上传协议</h2>
        <div className="segmented">
          {['s3', 'ftp', 'sftp'].map((protocol) => (
            <button
              key={protocol}
              className={upload.protocol === protocol ? 'selected' : ''}
              onClick={() => setUpload({ ...upload, protocol })}
            >
              {protocol.toUpperCase()}
            </button>
          ))}
        </div>
      </section>
      {upload.protocol === 's3' && (
        <section className="panel wide">
          <h2>S3 配置</h2>
          <div className="form-grid">
            <Field label="Endpoint" value={upload.s3.endpoint} onChange={(value) => setS3('endpoint', value)} placeholder="https://s3.example.com" />
            <Field label="Bucket" value={upload.s3.bucket} onChange={(value) => setS3('bucket', value)} />
            <Field label="Access Key" value={upload.s3.access_key} onChange={(value) => setS3('access_key', value)} />
            <Field label="Secret Key" value={upload.s3.secret_key} onChange={(value) => setS3('secret_key', value)} />
            <Field label="Region" value={upload.s3.region} onChange={(value) => setS3('region', value)} placeholder="auto" />
            <Field label="远程前缀" value={upload.s3.prefix} onChange={(value) => setS3('prefix', value)} placeholder="images/" />
            <Field label="公开域名" value={upload.s3.domain} onChange={(value) => setS3('domain', value)} placeholder="https://cdn.example.com" />
          </div>
        </section>
      )}
      {upload.protocol === 'ftp' && (
        <section className="panel wide">
          <h2>FTP 配置</h2>
          <div className="form-grid">
            <Field label="主机" value={upload.ftp.host} onChange={(value) => setFTP('host', value)} />
            <NumberField label="端口" value={upload.ftp.port} onChange={(value) => setFTP('port', value)} />
            <Field label="用户名" value={upload.ftp.username} onChange={(value) => setFTP('username', value)} />
            <Field label="密码" value={upload.ftp.password} onChange={(value) => setFTP('password', value)} />
            <Field label="远程目录" value={upload.ftp.remote_dir} onChange={(value) => setFTP('remote_dir', value)} placeholder="/public_html/images" />
            <Field label="访问地址" value={upload.ftp.base_url} onChange={(value) => setFTP('base_url', value)} placeholder="https://example.com/images" />
          </div>
        </section>
      )}
      {upload.protocol === 'sftp' && (
        <section className="panel wide">
          <h2>SFTP 配置</h2>
          <div className="form-grid">
            <Field label="主机" value={upload.sftp.host} onChange={(value) => setSFTP('host', value)} />
            <NumberField label="端口" value={upload.sftp.port} onChange={(value) => setSFTP('port', value)} />
            <Field label="用户名" value={upload.sftp.username} onChange={(value) => setSFTP('username', value)} />
            <Field label="密码" value={upload.sftp.password} onChange={(value) => setSFTP('password', value)} />
            <Field label="私钥路径" value={upload.sftp.key_path} onChange={(value) => setSFTP('key_path', value)} placeholder="C:/Users/me/.ssh/id_ed25519" />
            <Field label="远程目录" value={upload.sftp.remote_dir} onChange={(value) => setSFTP('remote_dir', value)} placeholder="/var/www/images" />
            <Field label="访问地址" value={upload.sftp.base_url} onChange={(value) => setSFTP('base_url', value)} placeholder="https://example.com/images" />
            <Field label="域名根目录" value={upload.sftp.domain_root} onChange={(value) => setSFTP('domain_root', value)} placeholder="/var/www" />
          </div>
        </section>
      )}
      <section className="panel wide">
        <h2>上传结果</h2>
        <UploadResultPanel result={props.uploadResult} isUploading={props.isUploading} onClear={props.onClear} />
      </section>
    </div>
  );
}

function SettingsView(props: {
  config: AppConfig;
  setConfig: (value: AppConfig) => void;
  inputDir: string;
  outputDir: string;
  saveSettings: () => void;
}) {
  const proxy = props.config.upload.proxy;
  const setProxy = <K extends keyof AppConfig['upload']['proxy']>(key: K, value: AppConfig['upload']['proxy'][K]) => {
    props.setConfig({
      ...props.config,
      upload: {
        ...props.config.upload,
        proxy: {
          ...proxy,
          [key]: value,
        },
      },
    });
  };

  return (
    <div className="content-grid">
      <section className="panel">
        <h2>运行时</h2>
        <Field
          label="avifenc 目录"
          value={props.config.avifenc_path}
          onChange={(value) => props.setConfig({ ...props.config, avifenc_path: value })}
          placeholder="C:/Users/sakurajiamai/Desktop/code/ImageCompression/build/bin/windows-artifacts"
        />
      </section>
      <section className="panel wide">
        <h2>上传代理</h2>
        <Checkbox label="启用代理" checked={proxy.enabled} onChange={(checked) => setProxy('enabled', checked)} />
        <div className="form-grid">
          <SelectField
            label="协议"
            value={proxy.type}
            onChange={(value) => setProxy('type', value)}
            options={[
              ['socks5', 'SOCKS5'],
              ['http', 'HTTP CONNECT'],
            ]}
          />
          <Field label="代理主机" value={proxy.host} onChange={(value) => setProxy('host', value)} placeholder="127.0.0.1" />
          <NumberField label="端口" value={proxy.port} min={1} max={65535} onChange={(value) => setProxy('port', value)} />
          <Field label="用户名" value={proxy.username} onChange={(value) => setProxy('username', value)} />
          <Field label="密码" value={proxy.password} onChange={(value) => setProxy('password', value)} type="password" />
          <Field label="兼容 URL" value={proxy.url} onChange={(value) => setProxy('url', value)} placeholder="socks5://user:pass@127.0.0.1:7890" />
        </div>
      </section>
      <section className="panel">
        <h2>偏好</h2>
        <div className="segmented">
          {['light', 'dark', 'gray'].map((theme) => (
            <button
              key={theme}
              className={props.config.theme === theme ? 'selected' : ''}
              onClick={() => props.setConfig({ ...props.config, theme })}
            >
              {theme}
            </button>
          ))}
        </div>
        <button onClick={props.saveSettings}>保存设置</button>
      </section>
    </div>
  );
}

function HelpView() {
  return (
    <div className="content-grid">
      <section className="panel wide prose">
        <h2>应用概览</h2>
        <p>
          <strong>Image Compression</strong> 是一个基于 Go/Wails 的桌面图像处理工作台，把"扫描 → 整理 → 压缩 → 上传"四条独立步骤串成一条流水线。
          所有重活都由 Go 后端执行（目录遍历、avifenc/cwebp 调用、S3/FTP/SFTP 协议），前端只负责参数表单与结果展示。
        </p>
        <p>
          应用默认数据目录：<code>~/.imagecompression/config.json</code>，所有参数都会持久化到这里，下次启动自动加载。
        </p>
      </section>

      <section className="panel">
        <h2>准备</h2>
        <p>
          入口页。指定输入目录与（可选）输出目录，扫描后展示图片 / 视频 / 其他分类以及总体积。
          可一键重命名、清除 EXIF、生成新的整理目录，或直接进入压缩 / 上传流程。
        </p>
      </section>

      <section className="panel">
        <h2>压缩</h2>
        <p>
          选择输出格式（AVIF / WebP / JPEG），调整质量、速度、YUV、位深、缩放与并行数等参数。
          支持命令预览、单图试压、整目录批处理，以及原始 vs 压缩后的对比预览。
        </p>
      </section>

      <section className="panel">
        <h2>上传</h2>
        <p>
          三种协议：S3（兼容 MinIO / R2 / 阿里 OSS 等）、FTP、SFTP。
          每个协议都支持代理（SOCKS5 / HTTP CONNECT）、远程目录、公开域名。
          留空时默认使用源目录名作为子路径。
        </p>
      </section>

      <section className="panel">
        <h2>设置</h2>
        <p>
          配置 avifenc 可执行文件目录、上传代理（SOCKS5 / HTTP）、主题外观等。
          点击"保存设置"将数据写回 <code>~/.imagecompression/config.json</code>。
        </p>
      </section>

      <section className="panel wide prose">
        <h2>典型工作流</h2>
        <ol>
          <li>
            <strong>扫描</strong>：在"准备"页填入源目录（如
            <code>D:/photos/raw</code>），点击"扫描目录"，得到图片 / 视频列表与总体积。
          </li>
          <li>
            <strong>整理</strong>：选择是否重命名 / 清除 EXIF，生成 <code>*_prepared</code> 整理目录（不会修改原文件）。
          </li>
          <li>
            <strong>压缩</strong>：切到"压缩"页，确认输入目录为整理目录、输出目录为 <code>*_compressed</code>，选择 AVIF / WebP / JPEG 与参数。
            点击"压缩目录"批量处理，结果区可对比预览。
          </li>
          <li>
            <strong>上传</strong>：切到"上传"页，确认输入目录为压缩输出目录，填写协议参数后点击"开始上传"。
            也可在"准备"页直接使用"准备压缩上传"按钮一键走完全流程。
          </li>
        </ol>
      </section>

      <section className="panel wide prose">
        <h2>自定义上传路径</h2>
        <p>
          默认情况下，应用会把源目录的文件夹名作为远程子路径。例如源目录
          <code>album-2026</code> 会自动以 <code>album-2026/</code> 作为子路径。
        </p>
        <p>
          如果你希望上传到自定义路径（例如 <code>photos/2026/spring</code>），可以在"上传"页中的
          <strong>自定义远程子路径</strong> 字段直接填写，填写后优先级高于源目录名。
          留空时仍然沿用源目录名。
        </p>
        <p>
          该路径会拼接到所选协议的根路径后面：S3 的 <code>Prefix</code>、FTP/SFTP 的
          <code>RemoteDir</code> 都会自动附加这段子路径，方便你保持一个稳定的根目录结构。
        </p>
      </section>

      <section className="panel wide prose">
        <h2>常见问题</h2>
        <ul>
          <li>
            <strong>avifenc 找不到？</strong>在"设置"页填写 avifenc 所在目录（包含
            <code>avifenc.exe</code> 的文件夹），或在系统 PATH 中加入 avifenc 可执行文件路径。
          </li>
          <li>
            <strong>上传失败？</strong>先确认协议、主机、端口、凭据是否正确；启用代理时请检查代理主机与端口。
          </li>
          <li>
            <strong>压缩后体积没有变小？</strong>可能是源文件本身已经被高度压缩（如 JPEG 90+），可尝试调高
            <code>max_quality</code>、或切换到 AVIF。
          </li>
          <li>
            <strong>如何清空配置？</strong>删除 <code>~/.imagecompression/config.json</code> 即可恢复默认。
          </li>
        </ul>
      </section>
    </div>
  );
}

function Field(props: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string }) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <input
        type={props.type ?? 'text'}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
        placeholder={props.placeholder}
      />
    </label>
  );
}

function NumberField(props: { label: string; value: number; onChange: (value: number) => void; min?: number; max?: number }) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <input
        type="number"
        min={props.min}
        max={props.max}
        value={Number.isFinite(props.value) ? props.value : 0}
        onChange={(event) => props.onChange(Number(event.target.value))}
      />
    </label>
  );
}

function SelectField(props: { label: string; value: string; onChange: (value: string) => void; options: Array<[string, string]> }) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <select value={props.value} onChange={(event) => props.onChange(event.target.value)}>
        {props.options.map(([value, label]) => (
          <option value={value} key={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Checkbox(props: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="switch-row">
      <input type="checkbox" checked={props.checked} onChange={(event) => props.onChange(event.target.checked)} />
      <span>{props.label}</span>
    </label>
  );
}

function OperationList(props: { operations: PrepareOperation[] }) {
  if (!props.operations.length) {
    return <div className="empty-state">扫描目录后生成准备计划。</div>;
  }
  return (
    <div className="operation-list">
      {props.operations.slice(0, 8).map((operation) => (
        <div className="operation" key={`${operation.source}-${operation.destination}`}>
          <span>{operation.kind}</span>
          <strong>{basename(operation.source)}</strong>
          <em>{operation.destination}</em>
        </div>
      ))}
    </div>
  );
}

function UploadResultPanel(props: { result: UploadResult | null; isUploading: boolean; onClear: () => void }) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');
  if (!props.result) {
    return <div className="empty-state">填写目录与连接参数后开始上传。</div>;
  }
  const result = normalizeUploadResult(props.result);
  const progress = result.totalFiles > 0 ? Math.min(100, Math.round((result.uploadedFiles / result.totalFiles) * 100)) : 0;

  async function copyAllUrls() {
    if (!result.urls.length) return;
    const text = result.urls.join('\n');
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setCopyState('copied');
      setTimeout(() => setCopyState('idle'), 1500);
    } catch (error) {
      setCopyState('failed');
      setTimeout(() => setCopyState('idle'), 1500);
    }
  }

  return (
    <div className="result-stack">
      <div className="metric-grid">
        <div className="metric">
          <span>总文件</span>
          <strong>{result.totalFiles}</strong>
        </div>
        <div className="metric">
          <span>成功</span>
          <strong>{result.uploadedFiles}</strong>
        </div>
        <div className="metric">
          <span>失败</span>
          <strong>{result.failedFiles}</strong>
        </div>
        <div className="metric">
          <span>进度</span>
          <strong>{progress}%</strong>
        </div>
      </div>
      {result.totalFiles > 0 && (
        <div className="progress-track" aria-label="上传进度">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      )}
      {result.errors.length > 0 && (
        <div className="result-list error-list">
          {result.errors.slice(0, 8).map((error) => (
            <span key={error}>{error}</span>
          ))}
        </div>
      )}
      <div className="url-output">
        <div className="url-output-header">
          <h3>URL 输出</h3>
          <span className="url-output-count">{result.urls.length} 条</span>
        </div>
        <div className="url-output-list">
          {result.urls.length === 0 ? (
            <div className="empty-state">等待 URL 输出…</div>
          ) : (
            result.urls.map((url) => <span key={url} title={url}>{url}</span>)
          )}
        </div>
        <div className="url-output-footer">
          <button
            className="ghost-button"
            onClick={copyAllUrls}
            disabled={!result.urls.length}
            title="把全部链接按行复制到剪贴板"
          >
            <Copy size={16} />
            {copyState === 'copied' ? '已复制' : copyState === 'failed' ? '复制失败' : '全部复制'}
          </button>
          <button className="ghost-button" onClick={props.onClear} disabled={!result.urls.length && !result.errors.length}>
            清空
          </button>
        </div>
      </div>
      {props.isUploading && (
        <p className="hint">正在上传，新 URL 会持续追加在下方…</p>
      )}
    </div>
  );
}

function CompressProgressPanel(props: { progress: CompressProgressEvent | null; isCompressing: boolean }) {
  if (!props.progress || props.progress.total === 0) {
    return <div className="empty-state">尚未开始压缩。</div>;
  }
  const progress = props.progress;
  const percent = progress.total > 0 ? Math.min(100, Math.round((progress.current / progress.total) * 100)) : 0;
  const speedText = progress.speed > 0 ? `${progress.speed.toFixed(1)} 张/秒` : '— 张/秒';
  const elapsedText = progress.elapsedSec > 0 ? `${progress.elapsedSec.toFixed(1)} 秒` : '—';

  return (
    <div className="result-stack">
      <div className="metric-grid">
        <div className="metric">
          <span>总文件</span>
          <strong>{progress.total}</strong>
        </div>
        <div className="metric">
          <span>已处理</span>
          <strong>{progress.current}</strong>
        </div>
        <div className="metric">
          <span>成功</span>
          <strong>{progress.compressed}</strong>
        </div>
        <div className="metric">
          <span>失败</span>
          <strong>{progress.failed}</strong>
        </div>
      </div>
      <div className="progress-track" aria-label="压缩进度">
        <div className="progress-bar" style={{ width: `${percent}%` }} />
      </div>
      <div className="progress-meta">
        <span>
          压缩: <strong>{progress.currentFile || '—'}</strong>
        </span>
        <span>
          速度: <strong>{speedText}</strong>
        </span>
        <span>
          进度: <strong>{percent}%</strong>
        </span>
        <span>
          用时: <strong>{elapsedText}</strong>
        </span>
      </div>
      {progress.error && (
        <p className="error-text">错误: {progress.error}</p>
      )}
      {!props.isCompressing && progress.done && (
        <p className="hint">压缩已完成，可在下方查看结果与预览。</p>
      )}
    </div>
  );
}

function CompressResultPanel(props: {
  result: CompressBatchResult | null;
  previewItems: PreviewItem[];
  previewImages: PreviewImages;
  onOpenPreviewItem: (item: PreviewItem) => void;
  onClear: () => void;
}) {
  if (!props.result) {
    return <div className="empty-state">选择格式和目录后开始批量压缩。</div>;
  }
  const result = normalizeCompressBatchResult(props.result);

  const ratio = result.originalSize > 0
    ? `${Math.max(0, 100 - (result.compressedSize / result.originalSize) * 100).toFixed(1)}%`
    : '-';

  return (
    <div className="result-stack">
      <div className="result-header">
        <h3>压缩结果</h3>
        <div className="result-header-actions">
          <span className="result-count">{result.compressedFiles}/{result.totalFiles} 成功</span>
          <button className="ghost-button" onClick={props.onClear}>清空</button>
        </div>
      </div>
      <div className="metric-grid">
        <div className="metric">
          <span>总文件</span>
          <strong>{result.totalFiles}</strong>
        </div>
        <div className="metric">
          <span>成功</span>
          <strong>{result.compressedFiles}</strong>
        </div>
        <div className="metric">
          <span>跳过</span>
          <strong>{result.skippedFiles}</strong>
        </div>
        <div className="metric">
          <span>失败</span>
          <strong>{result.failedFiles}</strong>
        </div>
        <div className="metric">
          <span>节省</span>
          <strong>{ratio}</strong>
        </div>
        <div className="metric">
          <span>原始 → 压缩</span>
          <strong>{`${formatSize(result.originalSize)} → ${formatSize(result.compressedSize)}`}</strong>
        </div>
      </div>
      <div className="placeholder-list">
        <span>输出目录：{result.outputDir}</span>
      </div>
      {props.previewItems.length > 0 && (
        <div className="preview-list">
          {props.previewItems.map((item) => (
            <button className="preview-row" key={`${item.inputPath}-${item.outputPath}`} onClick={() => props.onOpenPreviewItem(item)}>
              <div>
                <span>原始</span>
                <strong>{basename(item.inputPath)}</strong>
                <em>{item.inputPath}</em>
              </div>
              <div>
                <span>压缩后</span>
                <strong>{basename(item.outputPath)}</strong>
                <em>{item.outputPath}</em>
              </div>
              <b>{item.savedPercent.toFixed(1)}%</b>
            </button>
          ))}
        </div>
      )}
      {props.previewImages && (
        <div className="image-preview-grid">
          <figure>
            <figcaption>原始图片</figcaption>
            <img src={props.previewImages.original} alt={`原始图片 ${basename(props.previewImages.item.inputPath)}`} />
          </figure>
          <figure>
            <figcaption>压缩后</figcaption>
            <img src={props.previewImages.compressed} alt={`压缩后 ${basename(props.previewImages.item.outputPath)}`} />
          </figure>
        </div>
      )}
      {result.errors.length > 0 && (
        <div className="result-list error-list">
          {result.errors.slice(0, 8).map((error) => (
            <span key={error}>{error}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function tabTitle(tab: TabKey) {
  return {
    prepare: '准备工作台',
    compress: '压缩参数',
    upload: '上传通道',
    settings: '应用设置',
    help: '使用说明',
  }[tab];
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function buildAVIFParams(config: AppConfig): AVIFParams {
  const extra: Record<string, string | number | boolean> = {
    min_quality: config.compress.avif.min_quality,
    max_quality: config.compress.avif.max_quality,
    threads: config.compress.avif.threads,
    yuv: config.compress.avif.yuv,
    depth: config.compress.avif.depth,
    progressive: config.compress.avif.progressive,
  };
  if (config.compress.avif.alpha_enabled) {
    extra.alpha_min = config.compress.avif.alpha_min;
    extra.alpha_max = config.compress.avif.alpha_max;
  }

  return {
    Quality: config.compress.avif.max_quality,
    Speed: config.compress.avif.speed,
    Lossless: config.compress.avif.lossless,
    ResizeMode: config.compress.resize_mode,
    ResizeValue: config.compress.resize_value,
    KeepAspectRatio: config.compress.keep_aspect_ratio,
    StripExif: true,
    KeepICC: false,
    StripXMP: true,
    Extra: extra,
  };
}

function buildCompressParams(config: AppConfig): AVIFParams {
  if (config.compress.format === 'avif') {
    return buildAVIFParams(config);
  }
  return {
    Quality: config.compress.webp_jpeg.quality,
    Speed: config.compress.avif.speed,
    Lossless: config.compress.format === 'webp' && config.compress.webp_jpeg.lossless,
    ResizeMode: config.compress.resize_mode,
    ResizeValue: config.compress.resize_value,
    KeepAspectRatio: config.compress.keep_aspect_ratio,
    StripExif: true,
    KeepICC: false,
    StripXMP: true,
    Extra: {},
  };
}

function basename(path: string) {
  return path.split(/[\\/]/).pop() ?? path;
}

function normalizeScanResult(result: Partial<ScanResult>): ScanResult {
  return {
    baseDir: result.baseDir ?? '',
    images: result.images ?? [],
    videos: result.videos ?? [],
    others: result.others ?? [],
    totalSize: result.totalSize ?? 0,
    subdirs: result.subdirs ?? 0,
  };
}

function normalizeCompressBatchResult(result: Partial<CompressBatchResult>): CompressBatchResult {
  return {
    totalFiles: result.totalFiles ?? 0,
    compressedFiles: result.compressedFiles ?? 0,
    skippedFiles: result.skippedFiles ?? 0,
    failedFiles: result.failedFiles ?? 0,
    outputDir: result.outputDir ?? '',
    originalSize: result.originalSize ?? 0,
    compressedSize: result.compressedSize ?? 0,
    elapsedSeconds: result.elapsedSeconds ?? 0,
    results: result.results ?? [],
    errors: result.errors ?? [],
  };
}

function normalizeUploadResult(result: Partial<UploadResult>): UploadResult {
  return {
    totalFiles: result.totalFiles ?? 0,
    uploadedFiles: result.uploadedFiles ?? 0,
    failedFiles: result.failedFiles ?? 0,
    urls: result.urls ?? [],
    errors: result.errors ?? [],
  };
}

type UploadProgressEvent = {
  current: number;
  total: number;
  message: string;
  url?: string;
  error?: string;
  start?: boolean;
  done?: boolean;
  uploaded: number;
  failed: number;
  sourceDir: string;
};

function parseUploadEvent(raw: unknown): UploadProgressEvent | null {
  if (typeof raw !== 'string') {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as UploadProgressEvent;
    if (typeof parsed !== 'object' || parsed === null) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

type CompressProgressEvent = {
  current: number;
  total: number;
  currentFile: string;
  message: string;
  outputPath?: string;
  url?: string;
  error?: string;
  start?: boolean;
  done?: boolean;
  compressed: number;
  skipped: number;
  failed: number;
  original: number;
  compressedSize: number;
  speed: number;
  elapsedSec: number;
};

function parseCompressEvent(raw: unknown): CompressProgressEvent | null {
  if (typeof raw !== 'string') {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as CompressProgressEvent;
    if (typeof parsed !== 'object' || parsed === null) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

class ErrorBoundary extends Component<{ children: React.ReactNode }, { error: string | null }> {
  state = { error: null };

  static getDerivedStateFromError(error: unknown) {
    return { error: String(error) };
  }

  render() {
    if (this.state.error) {
      return (
        <main className="app-shell">
          <section className="workspace error-screen">
            <h1>界面渲染失败</h1>
            <p>{this.state.error}</p>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);
