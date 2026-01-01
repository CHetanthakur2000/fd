from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
from pathlib import Path
import threading
from urllib.parse import urlparse
from datetime import datetime, timedelta
import hashlib
import json
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import shutil
import time

app = Flask(__name__)

# HTML Template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Downloader - Download Your Favorite Videos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            color: #333;
        }
        
        /* Dark Mode */
        body.dark-mode {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
        }
        
        body.dark-mode .card {
            background: #2d2d44;
            color: #e0e0e0;
        }
        
        body.dark-mode label {
            color: #e0e0e0;
        }
        
        body.dark-mode input[type="text"],
        body.dark-mode select {
            background: #1a1a2e;
            color: #e0e0e0;
            border-color: #444;
        }
        
        body.dark-mode input[type="text"]:focus,
        body.dark-mode select:focus {
            border-color: #667eea;
        }
        
        body.dark-mode .message {
            background: #3d3d5c;
            color: #e0e0e0;
        }
        
        body.dark-mode .file-item {
            background: #1a1a2e;
            color: #e0e0e0;
        }
        
        body.dark-mode .link-item {
            background: #1a1a2e;
            border-color: #667eea;
        }
        
        body.dark-mode footer {
            background: #1a1a2e;
            border-top-color: #667eea;
            color: #aaa;
        }
        
        body.dark-mode .quality-btn {
            background: #3d3d5c;
            border-color: #666;
            color: #e0e0e0;
        }
        
        body.dark-mode .quality-btn:hover,
        body.dark-mode .quality-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        body.dark-mode .status-card {
            background: linear-gradient(135deg, #2d3d5c 0%, #3d4d6c 100%);
        }
        
        .theme-toggle {
            position: absolute;
            right: 20px;
            top: 20px;
            background: white;
            border: 2px solid #667eea;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.2em;
            transition: all 0.3s ease;
        }
        
        .theme-toggle:hover {
            background: #667eea;
            color: white;
        }
        
        body.dark-mode .theme-toggle {
            background: #2d2d44;
            color: white;
        }
        
        
        header {
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #667eea;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        header h1 {
            color: #fff;
            font-size: 2.5em;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        header p {
            color: #ddd;
            font-size: 1.1em;
        }
        
        .container {
            max-width: 1200px;
            margin: 30px auto;
            width: 95%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            header h1 {
                font-size: 2em;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                margin: 15px auto;
                width: 98%;
            }
            
            header {
                padding: 15px;
            }
            
            header h1 {
                font-size: 1.5em;
            }
            
            header p {
                font-size: 0.9em;
            }
            
            .card {
                padding: 15px;
                border-radius: 8px;
            }
            
            .quality-options {
                flex-direction: column;
            }
            
            .quality-btn {
                min-width: auto;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
            
            .theme-toggle {
                right: 10px;
                top: 10px;
                padding: 5px 10px;
                font-size: 1em;
            }
            
            button {
                padding: 10px 15px;
                font-size: 0.95em;
            }
            
            footer {
                padding: 15px;
                font-size: 0.85em;
            }
        }
        
        @media (max-width: 480px) {
            body {
                font-size: 14px;
            }
            
            header h1 {
                font-size: 1.3em;
                margin-bottom: 3px;
            }
            
            header p {
                font-size: 0.8em;
            }
            
            .container {
                margin: 10px auto;
                gap: 15px;
            }
            
            .card {
                padding: 12px;
                box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
            }
            
            .card h2 {
                font-size: 1.3em;
            }
            
            input[type="text"],
            select {
                padding: 10px;
                font-size: 16px;
            }
            
            .file-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .file-item a {
                width: 100%;
                justify-content: center;
            }
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        input[type="text"],
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }
        
        input[type="text"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
            margin-top: 10px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-weight: 500;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .info-section {
            grid-column: 1 / -1;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        
        .info-item h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .info-item p {
            font-size: 0.95em;
            line-height: 1.6;
        }
        
        .features-list {
            list-style: none;
            margin-top: 15px;
        }
        
        .features-list li {
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
            color: #333;
            line-height: 1.6;
        }
        
        .features-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .links-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .link-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .link-item:hover {
            background: #e7f0ff;
            transform: translateX(5px);
        }
        
        .link-item a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .link-item a:hover {
            color: #764ba2;
        }
        
        .status-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .status-card .status-indicator {
            width: 15px;
            height: 15px;
            background: #4ade80;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .file-list {
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .file-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #667eea;
        }
        
        .file-size {
            color: #666;
            font-size: 0.9em;
        }
        
        .spinner {
            display: none;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        
        .spinner.active {
            display: block;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        footer {
            background: rgba(0, 0, 0, 0.8);
            color: #ddd;
            text-align: center;
            padding: 20px;
            margin-top: auto;
            border-top: 3px solid #667eea;
        }
        
        footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        footer a:hover {
            text-decoration: underline;
        }
        
        .quality-options {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .quality-btn {
            flex: 1;
            min-width: 100px;
            padding: 10px;
            background: #f0f0f0;
            border: 2px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .quality-btn:hover,
        .quality-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .loading-bar {
            width: 100%;
            height: 4px;
            background: #ddd;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
            display: none;
        }
        
        .loading-bar.active {
            display: block;
        }
        
        .loading-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
    
    <header>
        <h1>🎬 Video Downloader Pro</h1>
        <p>Download videos from your favorite platforms with ease</p>
    </header>
    
    <div class="container">
        <div class="card">
            <h2>📥 Download Video</h2>
            
            <div id="message"></div>
            
            <form id="downloadForm">
                <div class="form-group">
                    <label for="videoUrl">Video URL (or Playlist URL)</label>
                    <input type="text" id="videoUrl" placeholder="https://www.youtube.com/watch?v=... or playlist URL" required>
                    <small style="color: #666; margin-top: 5px; display: block;">💡 Tip: Paste video or playlist URL</small>
                </div>
                
                <button type="button" style="background: #667eea; color: white; padding: 10px; border-radius: 6px; border: none; cursor: pointer; margin-bottom: 15px; width: 100%; font-weight: 600;" onclick="previewVideo()">👁️ Preview Video Info</button>
                
                <div id="previewModal" style="display: none; background: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin-top: 0; color: #333;">📺 Video Preview</h4>
                    <div id="previewContent"></div>
                    <button type="button" onclick="closePreview()" style="background: #999; color: white; padding: 8px 15px; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px;">Close</button>
                </div>
                
                <div class="form-group">
                    <label>Format</label>
                    <select id="formatSelect" onchange="updateFormatInfo()">
                        <option value="mp4">📹 MP4 (Video) - Most Compatible</option>
                        <option value="mkv">📹 MKV (Video) - High Quality</option>
                        <option value="webm">📹 WebM (Video) - Web Format</option>
                        <option value="mp3">🎵 MP3 (Audio Only)</option>
                    </select>
                    <small id="formatHint" style="color: #666; margin-top: 5px; display: block;">MP4 is best for mobile devices</small>
                </div>
                
                <div class="form-group">
                    <label id="qualityLabel">Quality <span id="qualitySize" style="color: #999;">(est. size)</span></label>
                    <div class="quality-options" id="qualityContainer">
                        <button type="button" class="quality-btn" data-quality="4k" data-size="500-2000MB" onclick="selectQuality(this)">4K ⚡<br><small>500-2000MB</small></button>
                        <button type="button" class="quality-btn active" data-quality="1080" data-size="300-800MB" onclick="selectQuality(this)">1080p<br><small>300-800MB</small></button>
                        <button type="button" class="quality-btn" data-quality="720" data-size="150-400MB" onclick="selectQuality(this)">720p<br><small>150-400MB</small></button>
                        <button type="button" class="quality-btn" data-quality="480" data-size="50-150MB" onclick="selectQuality(this)">480p<br><small>50-150MB</small></button>
                        <button type="button" class="quality-btn" data-quality="best" data-size="Auto" onclick="selectQuality(this)">Best<br><small>Auto</small></button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>⏱️ Schedule Download (Optional)</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <input type="date" id="scheduleDate" style="padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                        <input type="time" id="scheduleTime" style="padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                </div>
                
                <div class="loading-bar" id="loadingBar">
                    <div class="loading-bar-fill"></div>
                </div>
                
                <div class="spinner" id="spinner"></div>
                
                <button type="submit" id="submitBtn">⬇️ Download Now</button>
            </form>
        </div>
        
        <div class="card">
            <h2>📊 Service Status</h2>
            
            <div id="statusContent" class="status-card">
                <p><span class="status-indicator"></span> Loading...</p>
            </div>
            
            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; margin-bottom: 15px;">🌟 Key Features</h3>
                <ul class="features-list">
                    <li>Fast and reliable video downloading</li>
                    <li>Multiple quality options (360p to 1080p+)</li>
                    <li>Support for multiple platforms</li>
                    <li>Automatic retry on failures</li>
                    <li>Secure file management</li>
                    <li>Real-time download status</li>
                    <li>Large file support</li>
                    <li>Batch download capability</li>
                </ul>
            </div>
        </div>
        
        <div class="card info-section">
            <h2>ℹ️ About This Service</h2>
            
            <p style="color: #666; line-height: 1.8; margin-bottom: 20px;">
                Video Downloader Pro is a powerful and easy-to-use service that allows you to download videos from various platforms including YouTube, Vimeo, DailyMotion, and many others. With support for multiple quality options and advanced features, you can get your favorite videos in the format you want.
            </p>
            
            <div class="info-grid">
                <div class="info-item">
                    <h3>⚡ Lightning Fast</h3>
                    <p>Download videos at maximum speed with optimized infrastructure</p>
                </div>
                <div class="info-item">
                    <h3>🔒 Secure</h3>
                    <p>Your downloads are processed safely with no data storage</p>
                </div>
                <div class="info-item">
                    <h3>🎯 Reliable</h3>
                    <p>Advanced retry mechanisms ensure successful downloads</p>
                </div>
                <div class="info-item">
                    <h3>🌍 Universal</h3>
                    <p>Works with videos from virtually any platform online</p>
                </div>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">� Search YouTube</h3>
            <div class="form-group">
                <input type="text" id="searchQuery" placeholder="Search YouTube directly..." style="width: 100%; padding: 10px;">
                <button type="button" onclick="searchVideos()" style="margin-top: 10px; width: 100%; background: #667eea; color: white;">🔍 Search</button>
                <div id="searchResults" style="margin-top: 15px; max-height: 400px; overflow-y: auto;"></div>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">📺 Video Information</h3>
            <div class="form-group">
                <button type="button" onclick="getVideoMetadata()" style="width: 100%; background: #667eea; color: white;">📊 Get Video Info</button>
                <div id="metadataDisplay" style="margin-top: 15px; padding: 15px; background: #f5f5f5; border-radius: 6px; display: none;">
                    <div id="metadataContent"></div>
                </div>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">⚙️ Settings & Options</h3>
            <div class="form-group">
                <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; cursor: pointer;">
                    <input type="checkbox" id="enableNotifications"> 
                    🔔 Enable Download Notifications
                </label>
                <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; cursor: pointer;">
                    <input type="checkbox" id="downloadSubtitles"> 
                    📝 Download Subtitles
                </label>
                <div id="subtitleOptions" style="display: none; margin-left: 30px; margin-bottom: 10px;">
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <input type="radio" name="subtitleFormat" value="srt" checked> SRT Format
                    </label>
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <input type="radio" name="subtitleFormat" value="vtt"> VTT Format
                    </label>
                </div>
            </div>
            
            <div class="form-group">
                <label for="languageSelect">🌍 Language</label>
                <select id="languageSelect" onchange="changeLanguage(this.value)" style="width: 100%;">
                    <option value="en">English</option>
                    <option value="hi">हिंदी (Hindi)</option>
                    <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; margin-bottom: 10px;">
                    <input type="checkbox" id="darkModeSchedule"> 
                    🌙 Schedule Dark Mode
                </label>
                <div id="scheduleOptions" style="display: none; margin-left: 30px;">
                    <label>Sunset Time (HH:MM):
                        <input type="time" id="sunsetTime" value="18:00" style="width: 100%; padding: 8px; margin-top: 5px;">
                    </label>
                    <label style="margin-top: 10px; display: block;">Sunrise Time (HH:MM):
                        <input type="time" id="sunriseTime" value="06:00" style="width: 100%; padding: 8px; margin-top: 5px;">
                    </label>
                </div>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">🗑️ File Management</h3>
            <div class="form-group">
                <button type="button" onclick="cleanupOldFiles()" style="width: 100%; background: #ff6b6b; color: white; margin-bottom: 10px;">🧹 Clean Files Older Than 30 Days</button>
                <button type="button" onclick="openFileManager()" style="width: 100%; background: #667eea; color: white;">📂 Open File Manager</button>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">�🔗 Useful Links & Resources</h3>
            
            <div class="links-section">
                <div class="link-item">
                    <a href="javascript:showAPI()" title="View API Documentation">
                        📚 API Docs
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:listDownloads()" title="View downloaded files">
                        📂 My Downloads
                    </a>
                </div>
                <div class="link-item">
                    <a href="https://www.youtube.com" target="_blank">
                        ▶️ YouTube
                    </a>
                </div>
                <div class="link-item">
                    <a href="https://www.github.com" target="_blank">
                        💻 GitHub
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:showHelp()" title="Get help and FAQs">
                        ❓ Help & FAQs
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:contact()" title="Contact us">
                        📧 Contact Us
                    </a>
                </div>
            </div>
        </div>
        
        <div class="card" style="grid-column: 1 / -1;">
            <h2>📥 Recent Downloads</h2>
            <button onclick="loadDownloads()" style="margin-bottom: 20px;">Refresh Downloads</button>
            <div class="file-list" id="fileList">
                <p style="color: #999; text-align: center;">No downloads yet. Start downloading!</p>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Video Downloader Pro v1.0 | Made with ❤️ | &copy; 2025 All Rights Reserved</p>
        <p style="margin-top: 10px; font-size: 0.9em;">
            <a href="javascript:void(0)">Privacy Policy</a> | 
            <a href="javascript:void(0)">Terms of Service</a> | 
            <a href="javascript:void(0)">Contact</a>
        </p>
    </footer>
    
    <script>
        let selectedQuality = '1080';
        let selectedFormat = 'mp4';
        let selectedMP3Quality = '192';
        const VIDEO_CHUNK_SIZE = 10; // Videos per chunk in playlist
        
        // Quality estimates for different resolutions
        const qualityEstimates = {
            '4k': { video: '500-2000MB', audio: 'N/A' },
            '1080': { video: '300-800MB', audio: 'N/A' },
            '720': { video: '150-400MB', audio: 'N/A' },
            '480': { video: '50-150MB', audio: 'N/A' },
            'best': { video: 'Auto', audio: 'N/A' }
        };
        
        const mp3QualityInfo = {
            '128': { size: '5-30MB', bitrate: '128 kbps' },
            '192': { size: '8-45MB', bitrate: '192 kbps' },
            '256': { size: '10-60MB', bitrate: '256 kbps' },
            '320': { size: '15-80MB', bitrate: '320 kbps - Best Quality' }
        };
        
        // Dark Mode Toggle
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            updateThemeIcon();
        }
        
        function updateThemeIcon() {
            const btn = document.querySelector('.theme-toggle');
            if (document.body.classList.contains('dark-mode')) {
                btn.textContent = '☀️';
            } else {
                btn.textContent = '🌙';
            }
        }
        
        // Load theme preference
        window.addEventListener('load', () => {
            if (localStorage.getItem('theme') === 'dark') {
                document.body.classList.add('dark-mode');
            }
            updateThemeIcon();
            updateFormatInfo();
        });
        
        function selectQuality(btn) {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedQuality = btn.getAttribute('data-quality');
            updateQualityInfo();
        }
        
        function updateQualityInfo() {
            const quality = selectedQuality;
            const format = selectedFormat;
            
            if (format === 'mp3') {
                // MP3 quality info already shown in format hint
                return;
            }
            
            const estimate = qualityEstimates[quality];
            if (estimate) {
                const sizeSpan = document.getElementById('qualitySize');
                if (sizeSpan) {
                    sizeSpan.textContent = `(est. ${estimate.video})`;
                }
            }
        }
        
        function updateFormatInfo() {
            selectedFormat = document.getElementById('formatSelect').value;
            const formatHint = document.getElementById('formatHint');
            const qualityLabel = document.getElementById('qualityLabel');
            const qualityContainer = document.getElementById('qualityContainer');
            
            if (selectedFormat === 'mp3') {
                formatHint.innerHTML = '🎵 Select audio quality (bitrate affects size and sound quality)';
                qualityLabel.textContent = 'Audio Quality (Bitrate)';
                
                // Replace quality buttons with MP3 bitrate options
                qualityContainer.innerHTML = `
                    <button type="button" class="quality-btn" data-quality="mp3-128" onclick="selectMP3Quality(this)">128 kbps<br><small>5-30MB</small></button>
                    <button type="button" class="quality-btn active" data-quality="mp3-192" onclick="selectMP3Quality(this)">192 kbps<br><small>8-45MB ✓</small></button>
                    <button type="button" class="quality-btn" data-quality="mp3-256" onclick="selectMP3Quality(this)">256 kbps<br><small>10-60MB</small></button>
                    <button type="button" class="quality-btn" data-quality="mp3-320" onclick="selectMP3Quality(this)">320 kbps<br><small>15-80MB Best</small></button>
                `;
                selectedMP3Quality = '192';
            } else if (selectedFormat === 'mkv') {
                formatHint.innerHTML = '📹 Best for high-quality archival (larger files)';
                qualityLabel.textContent = 'Quality <span id="qualitySize" style="color: #999;">(est. size)</span>';
                
                // Restore video quality buttons
                qualityContainer.innerHTML = `
                    <button type="button" class="quality-btn" data-quality="4k" data-size="500-2000MB" onclick="selectQuality(this)">4K ⚡<br><small>500-2000MB</small></button>
                    <button type="button" class="quality-btn active" data-quality="1080" data-size="300-800MB" onclick="selectQuality(this)">1080p<br><small>300-800MB</small></button>
                    <button type="button" class="quality-btn" data-quality="720" data-size="150-400MB" onclick="selectQuality(this)">720p<br><small>150-400MB</small></button>
                    <button type="button" class="quality-btn" data-quality="480" data-size="50-150MB" onclick="selectQuality(this)">480p<br><small>50-150MB</small></button>
                    <button type="button" class="quality-btn" data-quality="best" data-size="Auto" onclick="selectQuality(this)">Best<br><small>Auto</small></button>
                `;
                selectedQuality = '1080';
                updateQualityInfo();
            } else if (selectedFormat === 'webm') {
                formatHint.innerHTML = '📹 Optimized for web browsers (good compression)';
                qualityLabel.textContent = 'Quality <span id="qualitySize" style="color: #999;">(est. size)</span>';
                
                qualityContainer.innerHTML = `
                    <button type="button" class="quality-btn" data-quality="4k" data-size="400-1500MB" onclick="selectQuality(this)">4K ⚡<br><small>400-1500MB</small></button>
                    <button type="button" class="quality-btn active" data-quality="1080" data-size="250-700MB" onclick="selectQuality(this)">1080p<br><small>250-700MB</small></button>
                    <button type="button" class="quality-btn" data-quality="720" data-size="120-350MB" onclick="selectQuality(this)">720p<br><small>120-350MB</small></button>
                    <button type="button" class="quality-btn" data-quality="480" data-size="40-120MB" onclick="selectQuality(this)">480p<br><small>40-120MB</small></button>
                    <button type="button" class="quality-btn" data-quality="best" data-size="Auto" onclick="selectQuality(this)">Best<br><small>Auto</small></button>
                `;
                selectedQuality = '1080';
                updateQualityInfo();
            } else {
                // MP4 - best for mobile
                formatHint.innerHTML = '✓ Best for mobile devices - most compatible format';
                qualityLabel.textContent = 'Quality <span id="qualitySize" style="color: #999;">(est. size)</span>';
                
                qualityContainer.innerHTML = `
                    <button type="button" class="quality-btn" data-quality="4k" data-size="500-2000MB" onclick="selectQuality(this)">4K ⚡<br><small>500-2000MB</small></button>
                    <button type="button" class="quality-btn active" data-quality="1080" data-size="300-800MB" onclick="selectQuality(this)">1080p<br><small>300-800MB</small></button>
                    <button type="button" class="quality-btn" data-quality="720" data-size="150-400MB" onclick="selectQuality(this)">720p<br><small>150-400MB</small></button>
                    <button type="button" class="quality-btn" data-quality="480" data-size="50-150MB" onclick="selectQuality(this)">480p<br><small>50-150MB</small></button>
                    <button type="button" class="quality-btn" data-quality="best" data-size="Auto" onclick="selectQuality(this)">Best<br><small>Auto</small></button>
                `;
                selectedQuality = '1080';
                updateQualityInfo();
            }
        }
        
        function selectMP3Quality(btn) {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const qualityStr = btn.getAttribute('data-quality');
            selectedMP3Quality = qualityStr.split('-')[1];
        }
        
        // Handle subtitle download toggle
        document.getElementById('downloadSubtitles')?.addEventListener('change', function() {
            document.getElementById('subtitleOptions').style.display = this.checked ? 'block' : 'none';
        });
        
        // Handle dark mode schedule toggle
        document.getElementById('darkModeSchedule')?.addEventListener('change', function() {
            document.getElementById('scheduleOptions').style.display = this.checked ? 'block' : 'none';
            if (this.checked) {
                saveDarkModeSchedule();
            }
        });
        
        // Change language - NO RELOAD (just save preference)
        function changeLanguage(lang) {
            localStorage.setItem('language', lang);
            showMessage('✅ Language changed to: ' + lang, 'success');
            // UI text would update based on language - implement as needed
        }
        
        // Search YouTube
        async function searchVideos() {
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) {
                showMessage('Enter a search query', 'error');
                return;
            }
            
            try {
                showMessage('🔍 Searching YouTube...', 'info');
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, max_results: 10 })
                });
                
                const data = await response.json();
                if (data.status === 'success' && data.results.length > 0) {
                    let html = '<div style="display: grid; gap: 10px;">';
                    data.results.forEach(video => {
                        html += `
                            <div style="background: #f5f5f5; padding: 10px; border-radius: 6px; cursor: pointer;" onclick="setVideoUrl('${video.url}')">
                                ${video.thumbnail ? `<img src="${video.thumbnail}" style="width: 100%; height: 100px; object-fit: cover; border-radius: 4px; margin-bottom: 5px;">` : ''}
                                <p style="margin: 5px 0; font-weight: 600;">${video.title}</p>
                                <small style="color: #999;">⏱️ ${Math.floor(video.duration / 60)} min | Click to download</small>
                            </div>
                        `;
                    });
                    html += '</div>';
                    document.getElementById('searchResults').innerHTML = html;
                    showMessage(`✅ Found ${data.results.length} results`, 'success');
                } else {
                    showMessage('No results found', 'error');
                }
            } catch (err) {
                showMessage('Search error: ' + err.message, 'error');
            }
        }
        
        function setVideoUrl(url) {
            document.getElementById('videoUrl').value = url;
            document.getElementById('searchResults').innerHTML = '';
            document.getElementById('searchQuery').value = '';
            showMessage('✅ Video URL set. Ready to download!', 'success');
        }
        
        // Get video metadata
        async function getVideoMetadata() {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url) {
                showMessage('Please enter a video URL first', 'error');
                return;
            }
            
            try {
                showMessage('📊 Fetching metadata...', 'info');
                const response = await fetch('/api/metadata', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    const meta = data.metadata;
                    const display = document.getElementById('metadataDisplay');
                    const dateStr = meta.upload_date ? `${meta.upload_date.slice(0,4)}-${meta.upload_date.slice(4,6)}-${meta.upload_date.slice(6,8)}` : 'Unknown';
                    const views = new Intl.NumberFormat().format(meta.view_count || 0);
                    
                    document.getElementById('metadataContent').innerHTML = `
                        <div style="display: grid; gap: 10px;">
                            ${meta.thumbnail ? `<img src="${meta.thumbnail}" style="width: 100%; max-height: 200px; border-radius: 6px; object-fit: cover;">` : ''}
                            <div>
                                <strong>📹 Title:</strong><br>${meta.title}
                            </div>
                            <div>
                                <strong>👤 Uploader:</strong><br>${meta.uploader}
                            </div>
                            <div>
                                <strong>📅 Upload Date:</strong><br>${dateStr}
                            </div>
                            <div>
                                <strong>👁️ Views:</strong><br>${views}
                            </div>
                            <div>
                                <strong>👍 Likes:</strong><br>${new Intl.NumberFormat().format(meta.like_count || 0)}
                            </div>
                            <div>
                                <strong>⏱️ Duration:</strong><br>${Math.floor(meta.duration / 60)} minutes ${Math.floor(meta.duration % 60)} seconds
                            </div>
                        </div>
                    `;
                    display.style.display = 'block';
                    showMessage('✅ Metadata loaded', 'success');
                } else {
                    showMessage(data.message || 'Failed to fetch metadata', 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        // Delete file
        async function deleteDownloadedFile(filename) {
            if (!confirm(`Delete "${filename}"?`)) return;
            
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    showMessage(`✅ ${data.message}`, 'success');
                    loadDownloads();
                } else {
                    showMessage(`❌ ${data.message}`, 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        // Clean up old files
        async function cleanupOldFiles() {
            if (!confirm('Delete files older than 30 days?')) return;
            
            try {
                showMessage('🧹 Cleaning up old files...', 'info');
                const response = await fetch('/api/cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ days: 30 })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    showMessage(`✅ Deleted ${data.files_deleted} old files`, 'success');
                    loadDownloads();
                } else {
                    showMessage(`❌ ${data.message}`, 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        // Open file manager - Opens Windows Explorer/File Manager
        function openFileManager() {
            showMessage('📂 Opening downloads folder...', 'info');
            fetch('/api/open-folder', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showMessage('✅ Downloads folder opened!', 'success');
                    } else {
                        showMessage('📂 See downloads folder in your browser', 'info');
                    }
                })
                .catch(() => showMessage('📂 Open your downloads folder manually', 'info'));
        }
        
        // Save dark mode schedule
        function saveDarkModeSchedule() {
            const sunset = document.getElementById('sunsetTime').value;
            const sunrise = document.getElementById('sunriseTime').value;
            
            localStorage.setItem('darkModeSchedule', JSON.stringify({
                sunset, sunrise, enabled: true
            }));
            
            showMessage('✅ Dark mode schedule saved', 'success');
            applyDarkModeSchedule();
        }
        
        // Apply dark mode based on schedule
        function applyDarkModeSchedule() {
            const schedule = localStorage.getItem('darkModeSchedule');
            if (!schedule) return;
            
            const { sunset, sunrise, enabled } = JSON.parse(schedule);
            const now = new Date();
            const currentTime = now.getHours() * 60 + now.getMinutes();
            const sunsetTime = parseInt(sunset.split(':')[0]) * 60 + parseInt(sunset.split(':')[1]);
            const sunriseTime = parseInt(sunrise.split(':')[0]) * 60 + parseInt(sunrise.split(':')[1]);
            
            if (enabled && currentTime >= sunsetTime || currentTime < sunriseTime) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            }
        }
        
        // Send browser notification
        function sendBrowserNotification(title, message) {
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(title, {
                    body: message,
                    icon: '🎬',
                    badge: '📥'
                });
            }
        }
        
        // Request notification permission
        function requestNotificationPermission() {
            if ('Notification' in window && Notification.permission === 'default') {
                Notification.requestPermission();
            }
        }
        
        // Check notification setting before download
        function getDownloadSubtitlesSettings() {
            return {
                enabled: document.getElementById('downloadSubtitles')?.checked || false,
                format: document.querySelector('input[name="subtitleFormat"]:checked')?.value || 'srt'
            };
        }
        
        // Initialize on page load
        window.addEventListener('load', () => {
            // Load saved language preference
            const savedLanguage = localStorage.getItem('language');
            if (savedLanguage) {
                document.getElementById('languageSelect').value = savedLanguage;
            }
            
            // Initialize notification permission
            if (document.getElementById('enableNotifications')?.checked) {
                requestNotificationPermission();
            }
            
            // Apply dark mode schedule
            applyDarkModeSchedule();
        });
        
        // Preview Video
        async function previewVideo() {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url) {
                showMessage('Please enter a URL first', 'error');
                return;
            }
            
            try {
                showMessage('📺 Fetching video info...', 'info');
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                
                const data = await response.json();
                if (response.ok && data.status === 'success') {
                    const info = data.info;
                    document.getElementById('previewContent').innerHTML = `
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            ${info.thumbnail ? `<img src="${info.thumbnail}" style="width: 100%; border-radius: 6px; margin-bottom: 10px; max-height: 300px; object-fit: cover;">` : ''}
                            <p><strong>📹 Title:</strong> ${info.title}</p>
                            <p><strong>⏱️ Duration:</strong> ${Math.floor(info.duration / 60)} minutes</p>
                            <p><strong>👁️ Views:</strong> ${info.views || 'N/A'}</p>
                            <p><strong>📅 Uploaded:</strong> ${info.upload_date || 'N/A'}</p>
                            ${info.is_playlist ? `<p style="color: #667eea; font-weight: 600;">📋 This is a PLAYLIST (${info.playlist_count} videos)</p>` : ''}
                        </div>
                    `;
                    document.getElementById('previewModal').style.display = 'block';
                    showMessage('✅ Preview loaded!', 'success');
                } else {
                    showMessage(data.message || 'Failed to load preview', 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        function closePreview() {
            document.getElementById('previewModal').style.display = 'none';
        }
        
        function showMessage(message, type = 'info') {
            const messageDiv = document.getElementById('message');
            messageDiv.className = 'message ' + type;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';
            
            if (type !== 'success') {
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
        }
        
        function showSpinner(show = true) {
            document.getElementById('spinner').classList.toggle('active', show);
            document.getElementById('loadingBar').classList.toggle('active', show);
            document.getElementById('submitBtn').disabled = show;
        }
        
        document.getElementById('downloadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('videoUrl').value.trim();
            const scheduleDate = document.getElementById('scheduleDate').value;
            const scheduleTime = document.getElementById('scheduleTime').value;
            
            if (!url) {
                showMessage('Please enter a valid URL', 'error');
                return;
            }
            
            // Check if scheduling
            if (scheduleDate && scheduleTime) {
                const scheduledTime = new Date(`${scheduleDate}T${scheduleTime}`);
                const now = new Date();
                
                if (scheduledTime <= now) {
                    showMessage('⏱️ Scheduled time must be in the future', 'error');
                    return;
                }
                
                showMessage(`✅ Download scheduled for ${scheduledTime.toLocaleString()}`, 'success');
                // In production, this would be stored in a database
                console.log(`Scheduled download for: ${scheduledTime}`);
                return;
            }
            
            showSpinner(true);
            showMessage('🚀 Initializing download...', 'info');
            
            try {
                const subtitleSettings = getDownloadSubtitlesSettings();
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        url: url,
                        quality: selectedFormat === 'mp3' ? selectedMP3Quality : selectedQuality,
                        format: selectedFormat,
                        is_playlist: url.includes('playlist'),
                        mp3_quality: selectedMP3Quality,
                        download_subtitles: subtitleSettings.enabled,
                        subtitle_format: subtitleSettings.format
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.status === 'started') {
                    document.getElementById('videoUrl').value = '';
                    showSpinner(false);
                    
                    // Create progress container if not exists
                    if (!document.getElementById('progressContainer')) {
                        const container = document.createElement('div');
                        container.id = 'progressContainer';
                        container.innerHTML = `
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; position: relative;">
                                <button onclick="this.parentElement.parentElement.remove()" style="position: absolute; right: 10px; top: 10px; background: transparent; border: none; font-size: 1.5em; cursor: pointer; color: white;">✕</button>
                                <div id="progressMessage" style="font-size: 1.1em; margin-bottom: 15px; font-weight: 600;">🚀 Starting download...</div>
                                <div id="progressBar" style="width: 100%; height: 20px; background: rgba(255,255,255,0.3); border-radius: 10px; overflow: hidden;">
                                    <div id="progressFill" style="width: 0%; height: 100%; background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); transition: width 0.3s ease;"></div>
                                </div>
                                <div id="progressPercent" style="margin-top: 10px; text-align: right; font-size: 0.9em; opacity: 0.9;">0%</div>
                            </div>
                        `;
                        document.getElementById('message').parentNode.insertBefore(container, document.getElementById('message').nextSibling);
                    }
                    
                    // Check status every 1 second with live updates
                    let attempts = 0;
                    let lastMessage = '';
                    
                    const statusInterval = setInterval(async () => {
                        attempts++;
                        try {
                            const statusResponse = await fetch(`/api/download-status/${data.task_id}`);
                            const statusData = await statusResponse.json();
                            
                            // Update progress bar
                            const progress = statusData.progress || 0;
                            const message = statusData.message || 'Processing...';
                            
                            if (message !== lastMessage) {
                                document.getElementById('progressMessage').textContent = message;
                                lastMessage = message;
                            }
                            
                            document.getElementById('progressFill').style.width = progress + '%';
                            document.getElementById('progressPercent').textContent = progress + '%';
                            
                            if (statusData.status === 'success') {
                                document.getElementById('progressFill').style.background = '#4ade80';
                                showMessage(`✅ ${statusData.message}`, 'success');
                                
                                // Send notification if enabled
                                if (document.getElementById('enableNotifications')?.checked) {
                                    sendBrowserNotification('✅ Download Complete', `${statusData.message}`);
                                }
                                
                                loadDownloads();
                                clearInterval(statusInterval);
                                setTimeout(() => {
                                    const container = document.getElementById('progressContainer');
                                    if (container) container.remove();
                                }, 3000);
                            } else if (statusData.status === 'error') {
                                document.getElementById('progressFill').style.background = '#ef4444';
                                showMessage(`❌ ${statusData.message}`, 'error');
                                
                                // Send error notification if enabled
                                if (document.getElementById('enableNotifications')?.checked) {
                                    sendBrowserNotification('❌ Download Failed', statusData.message);
                                }
                                
                                clearInterval(statusInterval);
                            } else if (statusData.status === 'partial') {
                                showMessage(`⚠️ ${statusData.message}`, 'success');
                                if (document.getElementById('enableNotifications')?.checked) {
                                    sendBrowserNotification('⚠️ Partial Download', statusData.message);
                                }
                                clearInterval(statusInterval);
                            }
                        } catch (err) {
                            console.error('Status check error:', err);
                        }
                        
                        // Continue checking for up to 5 minutes
                        if (attempts > 300) {
                            showMessage('⏱️ Download taking longer than expected. Check back soon!', 'info');
                            clearInterval(statusInterval);
                        }
                    }, 1000);
                } else {
                    showMessage(data.message || 'Failed to start download', 'error');
                    showSpinner(false);
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
                showSpinner(false);
            }
        });
        
        async function loadDownloads() {
            try {
                const response = await fetch('/api/downloads');
                const data = await response.json();
                
                const fileList = document.getElementById('fileList');
                
                if (data.files && data.files.length > 0) {
                    fileList.innerHTML = data.files.map(file => `
                        <div class="file-item">
                            <div style="flex: 1;">
                                <strong>${file.filename}</strong><br>
                                <span class="file-size">📦 ${file.size}</span>
                            </div>
                            <a href="/api/file/${encodeURIComponent(file.path)}" download style="color: #667eea; text-decoration: none; font-weight: 600; white-space: nowrap; margin-left: 10px;">
                                ⬇️ Download
                            </a>
                            <button type="button" onclick="deleteDownloadedFile('${file.path}')" style="background: #ff6b6b; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin-left: 10px; white-space: nowrap;">
                                🗑️ Delete
                            </button>
                        </div>
                    `).join('');
                } else {
                    fileList.innerHTML = '<p style="color: #999; text-align: center;">No downloads yet. Start downloading!</p>';
                }
            } catch (error) {
                document.getElementById('fileList').innerHTML = '<p style="color: #d32f2f; text-align: center;">Error loading downloads</p>';
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('statusContent').innerHTML = `
                    <h3>Server Status</h3>
                    <p style="margin: 15px 0;"><span class="status-indicator"></span> <strong>${data.status.toUpperCase()}</strong></p>
                    <p>Service: ${data.service}</p>
                    <p>Timeout: ${data.timeout}s</p>
                    <p>Max Retries: ${data.max_retries}</p>
                `;
            } catch (error) {
                document.getElementById('statusContent').innerHTML = '<p>Error loading status</p>';
            }
        }
        
        function showAPI() {
            alert('API Documentation\\n\\nEndpoints:\\n1. POST /api/download - Download video\\n2. GET /api/status - Service status\\n3. GET /api/downloads - List files\\n4. GET /api/file/<filename> - Download file');
        }
        
        function listDownloads() {
            loadDownloads();
        }
        
        function showHelp() {
            alert('Help & FAQs\\n\\n1. Paste video URL and select quality\\n2. Click Download Video\\n3. Wait for processing\\n4. Check My Downloads section\\n\\nSupported: YouTube, Vimeo, and more');
        }
        
        function contact() {
            alert('Contact Us\\n\\nEmail: support@example.com\\nWebsite: www.example.com\\nPhone: +1-xxx-xxx-xxxx');
        }
        
        // Load data on page load
        window.addEventListener('load', () => {
            updateStatus();
            loadDownloads();
        });
        
        // Refresh status every 30 seconds
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
"""

# Configuration
DOWNLOAD_DIR = "downloads"
MAX_RETRIES = 3
TIMEOUT = 300

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store download status
download_status = {}

# ==================== PROXY ROTATION SYSTEM ====================
# Free proxy list - rotates every 15 minutes
# Empty by default - users can add working proxies via /api/proxy/add endpoint
# Free proxies are unreliable and change frequently. Best options:
# 1. Add your own verified proxies via the API
# 2. Use a paid proxy service (more reliable)
# 3. Use a VPN instead of proxies
PROXY_LIST = []

class ProxyRotator:
    def __init__(self, proxy_list, rotation_interval=900):  # 900 seconds = 15 minutes
        self.proxy_list = proxy_list
        self.rotation_interval = rotation_interval
        self.current_index = 0
        self.last_rotation_time = time.time()
        self.current_proxy = None
        self.rotate_proxy()
    
    def rotate_proxy(self):
        """Rotate to next proxy in the list"""
        if not self.proxy_list:
            self.current_proxy = None
            self.last_rotation_time = time.time()
            return None
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        self.current_proxy = self.proxy_list[self.current_index]
        self.last_rotation_time = time.time()
        print(f"[Proxy] Rotated to proxy #{self.current_index + 1}: {self.current_proxy}")
        return self.current_proxy
    
    def get_proxy(self):
        """Get current proxy, rotate if 15 minutes passed"""
        current_time = time.time()
        if current_time - self.last_rotation_time >= self.rotation_interval:
            return self.rotate_proxy()
        return self.current_proxy
    
    def get_all_proxies(self):
        """Get list of all proxies"""
        return self.proxy_list
    
    def add_proxy(self, proxy_url):
        """Add new proxy to the rotation list"""
        if proxy_url not in self.proxy_list:
            self.proxy_list.append(proxy_url)
            return True
        return False
    
    def get_proxy_dict(self):
        """Get proxy as dict for yt-dlp"""
        proxy = self.get_proxy()
        if proxy:
            return {
                'http': proxy,
                'https': proxy,
            }
        return None

# Initialize proxy rotator
proxy_rotator = ProxyRotator(PROXY_LIST, rotation_interval=900)  # 15 minutes

# Languages configuration
LANGUAGES = {
    "en": {
        "title": "Video Downloader",
        "subtitle": "Download your favorite videos",
        "download": "Download",
        "quality": "Quality",
        "format": "Format",
        "mp3_quality": "MP3 Quality",
        "downloading": "Downloading...",
        "success": "Download successful!",
        "error": "Download error",
        "playlist": "Download entire playlist",
        "subtitles": "Download subtitles",
        "srt_format": "SRT (.srt)",
        "vtt_format": "VTT (.vtt)",
        "notifications": "Enable notifications",
        "metadata": "Video Information",
        "search": "Search YouTube",
        "delete": "Delete Files",
        "schedule_dark": "Schedule Dark Mode"
    },
    "hi": {
        "title": "वीडियो डाउनलोडर",
        "subtitle": "अपने पसंद के वीडियो डाउनलोड करें",
        "download": "डाउनलोड करें",
        "quality": "गुणवत्ता",
        "format": "प्रारूप",
        "mp3_quality": "MP3 गुणवत्ता",
        "downloading": "डाउनलोड हो रहा है...",
        "success": "डाउनलोड सफल!",
        "error": "डाउनलोड त्रुटि",
        "playlist": "पूरी प्लेलिस्ट डाउनलोड करें",
        "subtitles": "सबटाइटल डाउनलोड करें",
        "srt_format": "SRT (.srt)",
        "vtt_format": "VTT (.vtt)",
        "notifications": "सूचनाएं सक्षम करें",
        "metadata": "वीडियो जानकारी",
        "search": "YouTube खोजें",
        "delete": "फाइलें हटाएं",
        "schedule_dark": "डार्क मोड शेड्यूल करें"
    },
    "pa": {
        "title": "ਵਿਡੀਓ ਡਾਉਨਲੋਡਰ",
        "subtitle": "ਆਪਣੇ ਮਨਜ਼ੂਰ ਵੀਡੀਓ ਡਾਉਨਲੋਡ ਕਰੋ",
        "download": "ਡਾਉਨਲੋਡ ਕਰੋ",
        "quality": "ਗੁਣਵੱਤਾ",
        "format": "ਫਾਰਮੈਟ",
        "mp3_quality": "MP3 ਗੁਣਵੱਤਾ",
        "downloading": "ਡਾਉਨਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...",
        "success": "ਡਾਉਨਲੋਡ ਸਫਲ!",
        "error": "ਡਾਉਨਲੋਡ ਗਲਤੀ",
        "playlist": "ਪੂਰੀ ਪਲੇਲਿਸਟ ਡਾਉਨਲੋਡ ਕਰੋ",
        "subtitles": "ਸਬਟਾਈਟਲ ਡਾਉਨਲੋਡ ਕਰੋ",
        "srt_format": "SRT (.srt)",
        "vtt_format": "VTT (.vtt)",
        "notifications": "ਨੋਟਿਫਿਕੇਸ਼ਨ ਸਮਰਥ ਕਰੋ",
        "metadata": "ਵਿਡੀਓ ਜਾਣਕਾਰੀ",
        "search": "YouTube ਖੋਜ",
        "delete": "ਫਾਈਲਾਂ ਹਟਾਓ",
        "schedule_dark": "ਡਾਰਕ ਮੋਡ ਸ਼ਡਿਊਲ"
    }
}

# Download history and metadata storage
HISTORY_FILE = "download_history.json"
SETTINGS_FILE = "user_settings.json"

def load_download_history():
    """Load download history from file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_download_history(history):
    """Save download history to file"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_user_settings():
    """Load user settings"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"language": "en", "dark_mode_schedule": None, "notifications": False}
    return {"language": "en", "dark_mode_schedule": None, "notifications": False}

def save_user_settings(settings):
    """Save user settings"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving settings: {e}")

def download_subtitles(ydl, video_url, subtitle_format="srt"):
    """Download subtitles for a video"""
    try:
        subtitle_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitle_format': subtitle_format,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(subtitle_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return {"status": "success", "subtitles_downloaded": True}
    except Exception as e:
        return {"status": "error", "message": f"Subtitle download failed: {str(e)}"}

def extract_video_metadata(video_url):
    """Extract video metadata (title, uploader, date, views, etc.)"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            metadata = {
                "title": info.get('title', 'Unknown'),
                "uploader": info.get('uploader', 'Unknown'),
                "upload_date": info.get('upload_date', 'Unknown'),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "duration": info.get('duration', 0),
                "description": info.get('description', '')[:200],
                "thumbnail": info.get('thumbnail', '')
            }
            return {"status": "success", "metadata": metadata}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_notification(title, message, email=None):
    """Send notification (browser or email)"""
    try:
        # Email notification (optional)
        if email:
            try:
                msg = MIMEMultipart()
                msg['From'] = 'noreply@videodownloader.app'
                msg['To'] = email
                msg['Subject'] = title
                body = MIMEText(message)
                msg.attach(body)
                # Email sending code would go here
            except:
                pass
        return {"status": "success", "notification_sent": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_file_safe(filename):
    """Safely delete a downloaded file or folder (including playlist videos)"""
    try:
        # Handle both direct files and nested paths (like Playlist_1/video.mp4)
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Security check - prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(DOWNLOAD_DIR)):
            return {"status": "error", "message": "Invalid file path"}
        
        # Normalize path separators for cross-platform compatibility
        filepath = os.path.normpath(filepath)
        
        if os.path.isfile(filepath):
            os.remove(filepath)
            # Check if parent folder is empty and is a playlist folder
            parent_dir = os.path.dirname(filepath)
            if parent_dir != DOWNLOAD_DIR and os.path.isdir(parent_dir):
                try:
                    if not os.listdir(parent_dir):  # If folder is empty
                        os.rmdir(parent_dir)  # Remove empty folder
                except:
                    pass
            return {"status": "success", "message": f"File deleted: {filename}"}
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)
            return {"status": "success", "message": f"Folder deleted: {filename}"}
        else:
            return {"status": "error", "message": "File not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def search_youtube(query, max_results=10):
    """Search YouTube for videos"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        search_url = f"ytsearch{max_results}:{query}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            results = []
            for video in info.get('entries', []):
                results.append({
                    "id": video.get('id', ''),
                    "title": video.get('title', ''),
                    "url": f"https://www.youtube.com/watch?v={video.get('id', '')}",
                    "thumbnail": video.get('thumbnail', ''),
                    "duration": video.get('duration', 0)
                })
            return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}

def cleanup_old_files(days=30):
    """Clean up files older than specified days"""
    try:
        import time
        deleted_count = 0
        current_time = time.time()
        
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                file_time = os.path.getmtime(filepath)
                if current_time - file_time > days * 86400:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except:
                        pass
        
        return {"status": "success", "files_deleted": deleted_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def download_video_worker(url, quality="1080", task_id=None, format_type="mp4", is_playlist=False, mp3_quality="192", download_subtitles_flag=False, subtitle_format="srt"):
    """Background worker for downloading video or playlist"""
    try:
        # Validate URL
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            if task_id:
                download_status[task_id] = {"status": "error", "message": "Invalid URL format"}
            return {"status": "error", "message": "Invalid URL format"}
        
        # Update status - fetching info
        if task_id:
            download_status[task_id] = {
                "status": "downloading",
                "message": "🔍 Fetching video information...",
                "progress": 5
            }
        print(f"[Download] Checking available formats for: {url}")
        
        # Minimal options to just get info
        # Get current rotating proxy
        current_proxy = proxy_rotator.get_proxy()
        proxy_dict = proxy_rotator.get_proxy_dict()
        
        info_opts = {
            'quiet': False,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            'skip_download': True,
            'no_check_certificate': True,
            'prefer_insecure': True,
            'allow_unplayable_formats': True,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
        }
        
        # Add proxy if available
        if proxy_dict:
            info_opts['proxy'] = current_proxy
        
        # Get basic info first
        video_title = "Unknown"
        is_actual_playlist = False
        playlist_count = 0
        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                basic_info = ydl.extract_info(url, download=False)
                if basic_info:
                    video_title = basic_info.get('title', 'Unknown')
                    is_actual_playlist = 'entries' in basic_info
                    playlist_count = len(basic_info.get('entries', [])) if is_actual_playlist else 0
                    
                    if task_id:
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"📺 Found: {video_title}",
                            "progress": 10
                        }
                    print(f"[Download] Got basic info. Title: {video_title}, Playlist: {is_actual_playlist}, Count: {playlist_count}")
        except Exception as e:
            error_msg = str(e)[:150]
            print(f"[Download] Warning: Could not get basic info: {error_msg}")
            
            # Try rotating proxy on error
            if "proxy" in error_msg.lower() or "unable to connect" in error_msg.lower():
                next_proxy = proxy_rotator.rotate_proxy()
                if task_id:
                    download_status[task_id] = {
                        "status": "downloading",
                        "message": f"🔄 Proxy rotated. Retrying with new proxy...",
                        "progress": 8
                    }
            # Check if it's a YouTube player error
            elif "Failed to extract any player response" in error_msg or "player" in error_msg.lower():
                if task_id:
                    download_status[task_id] = {
                        "status": "downloading",
                        "message": f"⚠️ YouTube blocking requests. Rotating proxy...",
                        "progress": 8
                    }
            else:
                if task_id:
                    download_status[task_id] = {
                        "status": "downloading",
                        "message": f"⚠️ Fetching info (may take a moment)...",
                        "progress": 10
                    }
        
        # Progress hook for download updates
        def progress_hook(d):
            if task_id:
                if d['status'] == 'downloading':
                    # Calculate percentage
                    total = d.get('total_bytes', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    if total > 0:
                        percentage = min(int((downloaded / total) * 80) + 10, 90)
                        speed = d.get('_speed_str', 'Unknown')
                        eta = d.get('_eta_str', '?')
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"⬇️ Downloading: {speed} | ETA: {eta}",
                            "progress": percentage,
                            "title": video_title
                        }
                    else:
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"⬇️ Downloading... ({d.get('_speed_str', 'processing')})",
                            "progress": 15,
                            "title": video_title
                        }
                
                elif d['status'] == 'finished':
                    download_status[task_id] = {
                        "status": "downloading",
                        "message": "✅ Download complete, processing...",
                        "progress": 95,
                        "title": video_title
                    }
        
        # Handle playlist downloads with chunking
        if is_actual_playlist and is_playlist and playlist_count > 0:
            return download_playlist_chunked(url, quality, task_id, format_type, mp3_quality, playlist_count, video_title, progress_hook)
        
        # Select format based on quality preference
        format_map = {
            '4k': 'bestvideo[height>=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/best',
            '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            'best': 'bestvideo+bestaudio/best',
        }
        
        format_str = format_map.get(quality, 'best')
        
        # Handle MP3 format
        is_audio_only = format_type == 'mp3'
        if is_audio_only:
            format_str = 'bestaudio/best'
        
        # Set post-processors for format conversion
        postprocessors = []
        if is_audio_only:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': mp3_quality,
            })
        elif format_type == 'mkv':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mkv'
            })
        elif format_type == 'webm':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'webm'
            })
        else:
            # For MP4 format, ensure audio and video are combined properly
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            })
        
        # Handle playlist downloads
        nopl_arg = not is_playlist
        
        # Get current rotating proxy for download
        current_proxy = proxy_rotator.get_proxy()
        proxy_dict = proxy_rotator.get_proxy_dict()
        
        # Optimized for faster downloads with better headers and retry logic
        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'ignoreerrors': True,
            'no_color': True,
            'writesubtitles': download_subtitles_flag,
            'writeautomaticsub': download_subtitles_flag,
            'subtitle_format': subtitle_format if download_subtitles_flag else None,
            'postprocessors': postprocessors,
            'progress_hooks': [progress_hook],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            },
            'no_check_certificate': True,
            'prefer_insecure': True,
            'allow_unplayable_formats': True,
            'youtube_include_dash_manifest': True,
            'concurrent_fragment_downloads': 4,
            'ratelimit': 10000000,
            'noplaylist': nopl_arg,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'skip': ['hls']}},
        }
        
        # Add proxy if available
        if proxy_dict:
            ydl_opts['proxy'] = current_proxy
        
        if task_id:
            mode_text = "🎵 Extracting audio" if is_audio_only else "🎬 Starting video download"
            if is_playlist and is_actual_playlist:
                mode_text += " (Playlist mode)"
            download_status[task_id] = {
                "status": "downloading",
                "message": f"{mode_text}... (Proxy: {current_proxy})" if current_proxy else f"{mode_text}...",
                "progress": 15,
                "title": video_title
            }
        
        print(f"[Download] Starting download with format: {format_type}, Proxy: {current_proxy if current_proxy else 'None'}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Check if we got anything
            if info is None:
                # If download=True returns None, it might have still downloaded
                # Try to find the file anyway
                print(f"[Download] Info is None but checking for downloaded files...")
                
                error_msg = "Video download may have succeeded but info unavailable. Check downloads folder."
                if task_id:
                    download_status[task_id] = {"status": "partial", "message": error_msg}
                print(f"[Download] {error_msg}")
                return {"status": "partial", "message": error_msg}
            
            filename = ydl.prepare_filename(info)
            
            result = {
                "status": "success",
                "message": "✅ Download completed successfully!",
                "file": filename,
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 'N/A'),
                "progress": 100
            }
            
            if task_id:
                download_status[task_id] = result
            
            print(f"[Download] Completed: {filename}")
            return result
    
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        print(f"[Download Error] {error_str}")
        
        # Handle YouTube player extraction errors
        if "Failed to extract any player response" in error_str:
            error_msg = "⚠️ YouTube is blocking automated downloads. Try:\n1. Using a VPN\n2. Waiting a few minutes\n3. Trying with a different video"
        elif "Requested format is not available" in error_str or "not available" in error_str.lower():
            error_msg = "⚠️ YouTube format not available. Try:\n1. Selecting lower quality\n2. Using a VPN\n3. Trying another video"
        elif "Sign in to confirm you're not a bot" in error_str or "Sign in required" in error_str.lower():
            error_msg = "⚠️ YouTube requires sign-in/bot verification. Try:\n1. Using a VPN\n2. Waiting some time\n3. Trying a public video"
        elif "too many requests" in error_str.lower() or "rate limit" in error_str.lower():
            error_msg = "⚠️ Too many requests to YouTube. Please wait 5-10 minutes before trying again."
        else:
            error_msg = f"❌ Download error: {error_str[:80]}"
        
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        return {"status": "error", "message": error_msg}
    
    except yt_dlp.utils.ExtractorError as e:
        error_msg = "❌ Video is private, age-restricted, or region-blocked. Try another video."
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        print(f"[Download Error] {error_msg}")
        return {"status": "error", "message": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)[:80]}"
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        print(f"[Download Error] {error_msg}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": error_msg}

def download_playlist_chunked(url, quality, task_id, format_type, mp3_quality, playlist_count, playlist_title, progress_hook):
    """Download playlist in chunks of VIDEO_CHUNK_SIZE videos"""
    try:
        chunk_size = 10  # Videos per chunk
        num_chunks = (playlist_count + chunk_size - 1) // chunk_size
        
        all_downloaded = []
        
        for chunk_num in range(num_chunks):
            start_index = chunk_num * chunk_size
            end_index = min((chunk_num + 1) * chunk_size, playlist_count)
            
            if task_id:
                msg = f"📋 Downloading Playlist Chunk {chunk_num + 1} of {num_chunks} (videos {start_index + 1}-{end_index})"
                chunk_progress = int((chunk_num / num_chunks) * 100)
                download_status[task_id] = {
                    "status": "downloading",
                    "message": msg,
                    "progress": chunk_progress,
                    "title": f"{playlist_title} - Part {chunk_num + 1}/{num_chunks}"
                }
            
            print(f"[Playlist] Downloading chunk {chunk_num + 1} of {num_chunks}")
            
            # Download this chunk
            format_map = {
                '4k':'bestvideo[height>=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/best',
                '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
                'best': 'bestvideo+bestaudio/best',
            }
            
            format_str = format_map.get(quality, 'best')
            is_audio_only = format_type == 'mp3'
            if is_audio_only:
                format_str = 'bestaudio/best'
            
            postprocessors = []
            if is_audio_only:
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': mp3_quality,
                })
            elif format_type == 'mkv':
                postprocessors.append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mkv'
                })
            elif format_type == 'webm':
                postprocessors.append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'webm'
                })
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(DOWNLOAD_DIR, f'Playlist_{chunk_num + 1}', '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 20,
                'retries': 3,
                'fragment_retries': 3,
                'skip_unavailable_fragments': True,
                'ignoreerrors': True,
                'postprocessors': postprocessors,
                'progress_hooks': [progress_hook],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
                'no_check_certificate': True,
                'prefer_insecure': True,
                'allow_unplayable_formats': True,
                'noplaylist': False,
                'playliststart': start_index + 1,
                'playlistend': end_index,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        all_downloaded.append(f"Part {chunk_num + 1}")
            except Exception as e:
                print(f"[Playlist] Error downloading chunk {chunk_num + 1}: {str(e)[:80]}")
        
        if task_id:
            download_status[task_id] = {
                "status": "success",
                "message": f"✅ Playlist downloaded! {len(all_downloaded)} chunks completed",
                "progress": 100
            }
        
        return {
            "status": "success",
            "message": f"✅ Playlist downloaded in {len(all_downloaded)} parts!",
            "chunks": all_downloaded
        }
    
    except Exception as e:
        error_msg = f"❌ Playlist error: {str(e)[:80]}"
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg}
        return {"status": "error", "message": error_msg}

def download_video(url, quality="720"):
    """Download video from URL with specified quality (wrapper for sync calls)"""
    return download_video_worker(url, quality)



@app.route('/', methods=['GET'])
def home():
    """Serve the web interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/download', methods=['POST'])
def download():
    """Endpoint to download video or playlist"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        url = data.get('url').strip()
        quality = data.get('quality', '1080')
        format_type = data.get('format', 'mp4')
        is_playlist = data.get('is_playlist', False)
        mp3_quality = data.get('mp3_quality', '192')
        download_subtitles_flag = data.get('download_subtitles', False)
        subtitle_format = data.get('subtitle_format', 'srt')
        
        if not url:
            return jsonify({"status": "error", "message": "URL cannot be empty"}), 400
        
        # Create task ID for tracking
        import time
        task_id = f"task_{int(time.time() * 1000)}"
        download_status[task_id] = {"status": "downloading", "message": "Download in progress..."}
        
        # Start download in background thread
        thread = threading.Thread(target=download_video_worker, args=(url, quality, task_id, format_type, is_playlist, mp3_quality, download_subtitles_flag, subtitle_format))
        thread.daemon = True
        thread.start()
        
        # Immediately return task info (don't wait for download to complete)
        return jsonify({
            "status": "started",
            "message": "Download started in background",
            "task_id": task_id
        }), 202
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview_video():
    """Get video info for preview without downloading"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        url = data.get('url').strip()
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                return jsonify({"status": "error", "message": "Could not fetch video info"}), 400
            
            # Check if it's a playlist
            is_playlist = 'entries' in info
            playlist_count = len(info.get('entries', [])) if is_playlist else 0
            
            return jsonify({
                "status": "success",
                "info": {
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "views": info.get('view_count', 'N/A'),
                    "upload_date": info.get('upload_date', 'N/A'),
                    "thumbnail": info.get('thumbnail', ''),
                    "is_playlist": is_playlist,
                    "playlist_count": playlist_count,
                    "description": info.get('description', '')[:200] if info.get('description') else ''
                }
            }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Preview error: {str(e)[:80]}"}), 500


@app.route('/api/download-status/<task_id>', methods=['GET'])
def download_status_check(task_id):
    """Check status of a download task"""
    try:
        if task_id in download_status:
            return jsonify(download_status[task_id]), 200
        else:
            return jsonify({"status": "error", "message": "Task not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Check service status"""
    return jsonify({
        "status": "running",
        "service": "Flask Video Downloader Pro",
        "download_dir": DOWNLOAD_DIR,
        "max_retries": MAX_RETRIES,
        "timeout": TIMEOUT,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    """List all downloaded files (excludes duplicates and temporary files)"""
    try:
        files = []
        seen_files = set()  # Track unique files
        
        if os.path.exists(DOWNLOAD_DIR):
            for root, dirs, filenames in os.walk(DOWNLOAD_DIR):
                for filename in filenames:
                    # Skip temporary and duplicate files
                    if filename.endswith(('.part', '.ytdl', '.tmp', '.temp')):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    
                    # Create unique identifier for the file
                    file_hash = hashlib.md5(filepath.encode()).hexdigest()[:8]
                    
                    # Skip if we've already seen this filename in downloads
                    if filename not in seen_files:
                        if os.path.isfile(filepath):
                            try:
                                size = os.path.getsize(filepath)
                                # Format size nicely
                                if size > 1024 * 1024 * 1024:
                                    size_str = f"{size / (1024*1024*1024):.2f} GB"
                                elif size > 1024 * 1024:
                                    size_str = f"{size / (1024*1024):.2f} MB"
                                elif size > 1024:
                                    size_str = f"{size / 1024:.2f} KB"
                                else:
                                    size_str = f"{size} B"
                                
                                # Get relative path for display
                                rel_path = os.path.relpath(filepath, DOWNLOAD_DIR)
                                
                                files.append({
                                    "filename": filename,
                                    "path": rel_path,
                                    "size": size_str,
                                    "bytes": size
                                })
                                seen_files.add(filename)
                            except Exception as e:
                                print(f"Error getting file info: {e}")
        
        # Sort by size descending (largest first)
        files.sort(key=lambda x: x['bytes'], reverse=True)
        
        return jsonify({
            "status": "success",
            "count": len(files),
            "files": files
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['GET'])
def get_download(filename):
    """Download a file from downloads directory"""
    try:
        # Handle both flat and nested paths
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Security check - prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(DOWNLOAD_DIR)):
            return jsonify({"status": "error", "message": "Invalid file path"}), 403
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
        
        # Get just the filename for the download
        just_filename = os.path.basename(filepath)
        
        return send_file(filepath, as_attachment=True, download_name=just_filename)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metadata', methods=['POST'])
def get_metadata():
    """Get video metadata without downloading"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        url = data.get('url').strip()
        result = extract_video_metadata(url)
        return jsonify(result), 200 if result["status"] == "success" else 400
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search_videos():
    """Search YouTube for videos"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"status": "error", "message": "Search query is required"}), 400
        
        query = data.get('query').strip()
        max_results = data.get('max_results', 10)
        
        result = search_youtube(query, max_results)
        return jsonify(result), 200 if result["status"] == "success" else 400
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/delete', methods=['POST'])
def delete_file():
    """Delete a downloaded file"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({"status": "error", "message": "Filename is required"}), 400
        
        filename = data.get('filename').strip()
        result = delete_file_safe(filename)
        return jsonify(result), 200 if result["status"] == "success" else 400
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_downloads():
    """Clean up old downloaded files"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)
        
        result = cleanup_old_files(days)
        return jsonify(result), 200 if result["status"] == "success" else 400
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/open-folder', methods=['POST'])
def open_downloads_folder():
    """Open downloads folder in file manager"""
    try:
        import subprocess
        import platform
        
        downloads_path = os.path.abspath(DOWNLOAD_DIR)
        
        # Handle different operating systems
        if platform.system() == 'Windows':
            # Windows: Use explorer
            subprocess.Popen(f'explorer /select,"{downloads_path}"')
            return jsonify({"status": "success", "message": "Opening folder..."}), 200
        elif platform.system() == 'Darwin':
            # macOS: Use open command
            subprocess.Popen(['open', downloads_path])
            return jsonify({"status": "success", "message": "Opening folder..."}), 200
        elif platform.system() == 'Linux':
            # Linux: Try xdg-open (works on most Linux systems)
            subprocess.Popen(['xdg-open', downloads_path])
            return jsonify({"status": "success", "message": "Opening folder..."}), 200
        else:
            return jsonify({"status": "error", "message": "Unsupported OS"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    """Get or update user settings"""
    try:
        if request.method == 'GET':
            settings = load_user_settings()
            return jsonify({"status": "success", "settings": settings}), 200
        
        elif request.method == 'POST':
            data = request.get_json()
            settings = load_user_settings()
            
            # Update settings
            if 'language' in data:
                settings['language'] = data['language']
            if 'dark_mode_schedule' in data:
                settings['dark_mode_schedule'] = data['dark_mode_schedule']
            if 'notifications' in data:
                settings['notifications'] = data['notifications']
            if 'email' in data:
                settings['email'] = data['email']
            
            save_user_settings(settings)
            return jsonify({"status": "success", "settings": settings}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get available languages"""
    try:
        lang_list = {lang: LANGUAGES[lang]["title"] for lang in LANGUAGES.keys()}
        return jsonify({"status": "success", "languages": lang_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Get translation for UI text"""
    try:
        data = request.get_json()
        language = data.get('language', 'en')
        text_key = data.get('key', '')
        
        if language not in LANGUAGES:
            language = 'en'
        
        translation = LANGUAGES[language].get(text_key, text_key)
        return jsonify({"status": "success", "translation": translation}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/proxy/status', methods=['GET'])
def get_proxy_status():
    """Get current proxy rotation status"""
    try:
        current_proxy = proxy_rotator.get_proxy()
        time_since_rotation = time.time() - proxy_rotator.last_rotation_time
        time_until_rotation = max(0, proxy_rotator.rotation_interval - time_since_rotation)
        
        return jsonify({
            "status": "success",
            "current_proxy": current_proxy,
            "proxy_index": proxy_rotator.current_index + 1,
            "total_proxies": len(proxy_rotator.proxy_list),
            "rotation_interval": proxy_rotator.rotation_interval,
            "time_since_rotation": int(time_since_rotation),
            "time_until_next_rotation": int(time_until_rotation),
            "next_rotation_in_minutes": round(time_until_rotation / 60, 1)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/proxy/rotate', methods=['POST'])
def rotate_proxy_manually():
    """Manually rotate to next proxy"""
    try:
        new_proxy = proxy_rotator.rotate_proxy()
        return jsonify({
            "status": "success",
            "message": f"Rotated to new proxy",
            "new_proxy": new_proxy,
            "proxy_index": proxy_rotator.current_index + 1,
            "total_proxies": len(proxy_rotator.proxy_list)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/proxy/list', methods=['GET'])
def list_proxies():
    """List all available proxies"""
    try:
        proxies = proxy_rotator.get_all_proxies()
        current_index = proxy_rotator.current_index
        
        return jsonify({
            "status": "success",
            "total_proxies": len(proxies),
            "current_proxy_index": current_index + 1 if proxies else 0,
            "current_proxy": proxies[current_index] if proxies else None,
            "proxies": [{
                "index": i + 1,
                "url": proxy,
                "is_current": i == current_index
            } for i, proxy in enumerate(proxies)]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/proxy/add', methods=['POST'])
def add_proxy():
    """Add new proxy to rotation list"""
    try:
        data = request.get_json()
        if not data or 'proxy_url' not in data:
            return jsonify({"status": "error", "message": "proxy_url is required"}), 400
        
        proxy_url = data.get('proxy_url').strip()
        
        if proxy_rotator.add_proxy(proxy_url):
            return jsonify({
                "status": "success",
                "message": f"Proxy added successfully",
                "proxy": proxy_url,
                "total_proxies": len(proxy_rotator.proxy_list)
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Proxy already exists in list"
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("[*] VIDEO DOWNLOADER PRO - Starting Server")
    print("=" * 70)
    print(f"\n[+] Download Directory: {os.path.abspath(DOWNLOAD_DIR)}")
    print(f"[+] Configuration:")
    print(f"    - Max Retries: {MAX_RETRIES}")
    print(f"    - Timeout: {TIMEOUT}s")
    print(f"\n[+] Access the application at:")
    print(f"    -> http://localhost:5000")
    print(f"    -> http://127.0.0.1:5000")
    print(f"\n[+] API Endpoints:")
    print(f"    - GET  /              - Web Interface")
    print(f"    - POST /api/download  - Download video (JSON)")
    print(f"    - GET  /api/status    - Service status")
    print(f"    - GET  /api/downloads - List downloaded files")
    print(f"    - GET  /api/file/<filename> - Download a file")
    print(f"\n[+] Features:")
    print(f"    [OK] Beautiful web interface")
    print(f"    [OK] Multiple quality options")
    print(f"    [OK] Real-time status updates")
    print(f"    [OK] Download file management")
    print(f"    [OK] Error handling and retry logic")
    print(f"    [OK] Support for multiple video platforms")
    print("\n" + "=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
