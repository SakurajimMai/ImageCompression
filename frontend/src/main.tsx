import React, { Component, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Archive,
  CloudUpload,
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
      })
      .catch((error) => setStatus(`配置加载失败：${String(error)}`));
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
      setStatus(`批量压缩完成：${result.compressedFiles}/${result.totalFiles} 个文件成功。`);
    } catch (error) {
      setStatus(`批量压缩失败：${String(error)}`);
    }
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
    try {
      const result = await api.UploadDirectoryWithRoot(inputDir, recursive, config.upload, uploadRootDir || inputDir);
      setUploadResult(normalizeUploadResult(result));
      setStatus(`上传完成：${result.uploadedFiles}/${result.totalFiles} 个文件成功。`);
    } catch (error) {
      setStatus(`上传执行失败：${String(error)}`);
    }
  }

  async function saveSettings() {
    const api = backend();
    const nextConfig = {
      ...config,
      last_input_dir: inputDir,
      last_output_dir: outputDir,
    };
    setConfig(nextConfig);
    if (!api) {
      setStatus('浏览器预览模式：设置已保存在页面状态。');
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
            onPreviewCommand={previewCommand}
            onCompressFirstImage={compressFirstImage}
            onCompressDirectory={executeCompressDirectory}
            onOpenPreviewItem={openPreviewItem}
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
            onUpload={executeUpload}
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
  onPreviewCommand: () => void;
  onCompressFirstImage: () => void;
  onCompressDirectory: () => void;
  onOpenPreviewItem: (item: PreviewItem) => void;
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
          <button onClick={props.onCompressDirectory}>
            <Archive size={16} />
            压缩目录
          </button>
        </div>
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
  onUpload: () => void;
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
        <Checkbox label="递归上传子目录" checked={props.recursive} onChange={props.setRecursive} />
        <div className="button-row">
          <button onClick={props.onUpload}>
            <CloudUpload size={16} />
            开始上传
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
        <UploadResultPanel result={props.uploadResult} />
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
    <section className="panel prose">
      <h2>说明</h2>
      <p>当前项目只保留 Go/Wails 桌面版本，核心流程通过 Go 后端执行，界面由 React/Vite 渲染。</p>
      <p>已接入配置加载、目录扫描、准备执行、AVIF/WebP/JPEG 压缩、图片预览和 S3/FTP/SFTP 上传。</p>
    </section>
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

function UploadResultPanel(props: { result: UploadResult | null }) {
  if (!props.result) {
    return <div className="empty-state">填写目录与连接参数后开始上传。</div>;
  }
  const result = normalizeUploadResult(props.result);

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
      </div>
      {result.urls.length > 0 && (
        <div className="result-list">
          {result.urls.slice(0, 8).map((url) => (
            <span key={url}>{url}</span>
          ))}
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

function CompressResultPanel(props: {
  result: CompressBatchResult | null;
  previewItems: PreviewItem[];
  previewImages: PreviewImages;
  onOpenPreviewItem: (item: PreviewItem) => void;
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
          <span>失败</span>
          <strong>{result.failedFiles}</strong>
        </div>
        <div className="metric">
          <span>节省</span>
          <strong>{ratio}</strong>
        </div>
      </div>
      <div className="placeholder-list">
        <span>输出目录：{result.outputDir}</span>
        <span>{`体积：${formatSize(result.originalSize)} -> ${formatSize(result.compressedSize)}`}</span>
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
    help: '迁移说明',
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
