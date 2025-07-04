import { useState, useRef, useEffect, type ChangeEvent, type KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import './landingPage.css'

export default function LandingPage() {
    const [csvData, setCsvData] = useState<string | null>(null);
    const [error, setError] = useState<string>("");
    const [fileName, setFileName] = useState<string>("");
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [showResults, setShowResults] = useState<boolean>(false);
    const [processedResults, setProcessedResults] = useState<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Animation variants for consistent smooth animations
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.2
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: { opacity: 1, y: 0 }
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 40, scale: 0.95 },
        visible: { opacity: 1, y: 0, scale: 1 }
    };

    const floatVariants = {
        hidden: { opacity: 0, scale: 0.8 },
        visible: { opacity: 1, scale: 1 }
    };

    const staggerContainer = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.15,
                delayChildren: 0.3
            }
        }
    };

    // Scroll animation effect
    useEffect(() => {
        const handleScroll = () => {
            const scrollY = window.scrollY;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;

            // Calculate scroll progress (0 to 1)
            const scrollProgress = scrollY / (documentHeight - windowHeight);

            // Apply parallax effects to floating orbs
            const orb1 = document.querySelector('.orb-1') as HTMLElement;
            const orb2 = document.querySelector('.orb-2') as HTMLElement;
            const orb3 = document.querySelector('.orb-3') as HTMLElement;

            if (orb1) {
                orb1.style.transform = `translateY(${scrollY * 0.3}px) rotate(${scrollProgress * 360}deg)`;
            }
            if (orb2) {
                orb2.style.transform = `translateY(${scrollY * -0.2}px) rotate(${scrollProgress * -270}deg)`;
            }
            if (orb3) {
                orb3.style.transform = `translateY(${scrollY * 0.1}px) rotate(${scrollProgress * 180}deg)`;
            }

            // Apply scroll-based effects to background pattern
            const backgroundPattern = document.querySelector('.background-pattern') as HTMLElement;
            if (backgroundPattern) {
                backgroundPattern.style.transform = `translateY(${scrollY * -0.1}px)`;
            }

            // Apply scroll-based opacity to hero content
            const heroContent = document.querySelector('.hero-content') as HTMLElement;
            if (heroContent) {
                const fadeStart = 0;
                const fadeEnd = windowHeight * 0.5;
                const opacity = Math.max(0, Math.min(1, 1 - (scrollY - fadeStart) / (fadeEnd - fadeStart)));
                heroContent.style.opacity = opacity.toString();
            }

            // Animate particles based on scroll
            const particles = document.querySelectorAll('.particle');
            particles.forEach((particle, index) => {
                const speed = 0.5 + (index * 0.1); // Different speeds for each particle
                const translateY = scrollY * speed;
                const translateX = Math.sin(scrollProgress * Math.PI * 2 + index) * 20;
                (particle as HTMLElement).style.transform = `translate(${translateX}px, ${translateY}px) scale(${1 + scrollProgress * 0.5})`;
            });

            // Animate geometric shapes
            const shapes = document.querySelectorAll('.shape');
            shapes.forEach((shape, index) => {
                const speed = 0.2 + (index * 0.15);
                const rotation = scrollProgress * 180 + (index * 60);
                const scale = 1 + Math.sin(scrollProgress * Math.PI) * 0.3;
                (shape as HTMLElement).style.transform = `translateY(${scrollY * speed}px) rotate(${rotation}deg) scale(${scale})`;
            });

            // Add scroll-based effects to upload card
            const uploadCard = document.querySelector('.upload-card') as HTMLElement;
            if (uploadCard) {
                const cardOffset = uploadCard.offsetTop;
                const cardHeight = uploadCard.offsetHeight;
                const cardProgress = Math.max(0, Math.min(1, (scrollY - cardOffset + windowHeight) / (windowHeight + cardHeight)));

                if (cardProgress > 0 && cardProgress < 1) {
                    const glow = cardProgress * 0.3;
                    uploadCard.style.boxShadow = `0 20px 40px rgba(0, 0, 0, 0.1), 0 0 ${glow * 100}px rgba(139, 92, 246, ${glow})`;
                }
            }

            // Add dynamic background color shift based on scroll
            const landingContainer = document.querySelector('.landing-container') as HTMLElement;
            if (landingContainer) {
                const colorShift = Math.sin(scrollProgress * Math.PI * 2) * 0.05;
                const hue = 260 + (colorShift * 20); // Shift between purple and blue
                landingContainer.style.background = `hsl(${hue}, 15%, 4%)`;
            }

            // Animate feature cards on scroll
            const featureCards = document.querySelectorAll('.feature-card');
            featureCards.forEach((card, index) => {
                const cardElement = card as HTMLElement;
                const cardRect = cardElement.getBoundingClientRect();
                const cardVisible = cardRect.top < windowHeight && cardRect.bottom > 0;

                if (cardVisible) {
                    const cardProgress = Math.max(0, Math.min(1, 1 - (cardRect.top / windowHeight)));
                    const scale = 0.95 + (cardProgress * 0.05);
                    const translateY = (1 - cardProgress) * 30;
                    const opacity = Math.max(0.3, cardProgress);

                    cardElement.style.transform = `translateY(${translateY}px) scale(${scale})`;
                    cardElement.style.opacity = opacity.toString();
                }
            });
        };

        // Add scroll event listener
        window.addEventListener('scroll', handleScroll, { passive: true });

        // Initial call to set initial state
        handleScroll();

        // Cleanup
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsLoading(true);
        setError("");

        try {
            // Check if file is CSV
            if (file.type !== "text/csv" && !file.name.endsWith('.csv')) {
                throw new Error("Please upload a valid CSV file");
            }

            // Check file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                throw new Error("File size must be less than 10MB");
            }

            const reader = new FileReader();
            reader.onload = (event: ProgressEvent<FileReader>) => {
                try {
                    const result = event.target?.result as string;
                    if (!result) {
                        throw new Error("Failed to read file");
                    }

                    // Basic CSV validation - check if it has commas and multiple lines
                    const lines = result.split('\n');
                    if (lines.length < 2) {
                        throw new Error("CSV file must contain at least a header row and one data row");
                    }

                    setCsvData(result);
                    setFileName(file.name);
                    setError("");
                } catch (parseError) {
                    setError("Invalid CSV format. Please check your file and try again.");
                    setCsvData(null);
                    setFileName("");
                } finally {
                    setIsLoading(false);
                }
            };

            reader.onerror = () => {
                setError("Failed to read file. Please try again.");
                setIsLoading(false);
            };

            reader.readAsText(file);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
            setIsLoading(false);
        }
    };

    const handleProcessData = async () => {
        if (csvData) {
            setIsProcessing(true);
            setError("");

            try {
                // First, get an access token
                const tokenResponse = await fetch("http://localhost:8000/api/token", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                if (!tokenResponse.ok) {
                    throw new Error("Failed to get access token");
                }

                const tokenData = await tokenResponse.json();
                const accessToken = tokenData.access_token;

                // Send CSV data to FastAPI backend
                const response = await fetch("http://localhost:8000/api/process-csv-data", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${accessToken}`,
                    },
                    body: JSON.stringify({
                        filename: fileName,
                        data: csvData,
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Failed to process CSV data");
                }

                const result = await response.json();
                console.log("Processing result:", result);
                
                // Show success message or results
                if (result.success) {
                    setProcessedResults(result);
                    setShowResults(true);
                } else {
                    setError(result.message || "Processing failed");
                }
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "Failed to process your data. Please try again.";
                setError(errorMessage);
                console.error("Processing error:", err);
            } finally {
                setIsProcessing(false);
            }
        }
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
            fileInputRef.current?.click();
        }
    };

    const resetUpload = () => {
        setCsvData(null);
        setError("");
        setFileName("");
        setShowResults(false);
        setIsProcessing(false);
        setProcessedResults(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const downloadProcessedCSV = () => {
        if (!processedResults || !processedResults.processed_csv_data) return;

        const blob = new Blob([processedResults.processed_csv_data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `processed_${fileName}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    };

    return (
        <motion.div
            className="landing-container"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
        >
            {/* Background elements */}
            <motion.div
                className="background-pattern"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.1 }}
            >
                <motion.div
                    className="floating-orb orb-1"
                    variants={floatVariants}
                ></motion.div>
                <motion.div
                    className="floating-orb orb-2"
                    variants={floatVariants}
                ></motion.div>
                <motion.div
                    className="floating-orb orb-3"
                    variants={floatVariants}
                ></motion.div>
            </motion.div>

            {/* Scroll-based animated particles */}
            <motion.div
                className="scroll-particles"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1.2, delay: 0.3 }}
            >
                {[...Array(10)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="particle"
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 0.3, scale: 1 }}
                        transition={{
                            duration: 0.6,
                            delay: 0.5 + (i * 0.1),
                            ease: "easeOut"
                        }}
                    ></motion.div>
                ))}
            </motion.div>

            {/* Geometric shapes */}
            <motion.div
                className="geometric-shapes"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.8 }}
            >
                <motion.div
                    className="shape shape-1"
                    initial={{ opacity: 0, rotate: 0, scale: 0 }}
                    animate={{ opacity: 0.1, rotate: 45, scale: 1 }}
                    transition={{ duration: 1, delay: 1 }}
                ></motion.div>
                <motion.div
                    className="shape shape-2"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 0.1, scale: 1 }}
                    transition={{ duration: 1, delay: 1.2 }}
                ></motion.div>
                <motion.div
                    className="shape shape-3"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 0.1, scale: 1 }}
                    transition={{ duration: 1, delay: 1.4 }}
                ></motion.div>
            </motion.div>

            {/* Hero Section */}
            <motion.section
                className="hero-section"
                variants={itemVariants}
            >
                <div className="container">
                    <motion.div
                        className="hero-content"
                        variants={staggerContainer}
                        initial="hidden"
                        animate="visible"
                    >
                        <motion.div
                            className="badge"
                            variants={itemVariants}
                            transition={{ duration: 0.6, delay: 0.2 }}
                        >
                            <span className="badge-icon">🔍</span>
                            <span>Profile Verification System</span>
                        </motion.div>

                        <motion.h1
                            className="hero-title"
                            variants={itemVariants}
                            transition={{ duration: 0.8, delay: 0.4 }}
                        >
                            Ensure Verification
                            <span className="gradient-text"> Compliance & Accuracy</span>
                        </motion.h1>

                        <motion.p
                            className="hero-subtitle"
                            variants={itemVariants}
                            transition={{ duration: 0.6, delay: 0.6 }}
                        >
                            Upload your CSV file to validate profile verification details against
                            Standard Operating Procedures (SOP) and ensure data integrity.
                        </motion.p>
                    </motion.div>

                    {/* Upload Section - Only show when results are not displayed */}
                    <AnimatePresence>
                        {!showResults && (
                            <motion.div
                                className="upload-section"
                                variants={itemVariants}
                                initial="hidden"
                                animate="visible"
                                exit="hidden"
                                transition={{ duration: 0.8, delay: 0.8 }}
                            >
                                <motion.div
                                    className="upload-card"
                                    variants={cardVariants}
                                    initial="hidden"
                                    animate="visible"
                                    transition={{ duration: 0.9, delay: 1.0 }}
                                    whileHover={{ y: -5, transition: { duration: 0.2 } }}
                                >
                                    <motion.div
                                        className="upload-header"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.6, delay: 1.2 }}
                                    >
                                        <div className="upload-icon">📂</div>
                                        <h3 className="upload-title">Upload Profile Data</h3>
                                        <p className="upload-description">
                                            Upload your CSV file containing profile verification data
                                        </p>
                                    </motion.div>

                                    <motion.div
                                        className="upload-zone"
                                        role="button"
                                        tabIndex={0}
                                        onKeyDown={handleKeyPress}
                                        aria-label="Click to upload CSV file"
                                        onClick={() => fileInputRef.current?.click()}
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ duration: 0.6, delay: 1.4 }}
                                        whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept=".csv,text/csv"
                                            onChange={handleFileUpload}
                                            className="file-input"
                                            disabled={isLoading}
                                            aria-describedby={error ? "error-message" : undefined}
                                        />

                                        <div className="upload-content">
                                            <motion.div
                                                className="upload-visual"
                                                animate={{
                                                    y: [0, -10, 0],
                                                    transition: {
                                                        duration: 2,
                                                        repeat: Infinity,
                                                        ease: "easeInOut"
                                                    }
                                                }}
                                            >
                                                <div className="upload-circle">
                                                    <span className="upload-emoji">📤</span>
                                                </div>
                                            </motion.div>
                                            <div className="upload-text">
                                                <p className="upload-primary">Choose a CSV file</p>
                                                <p className="upload-secondary">or drag it here</p>
                                                <p className="upload-limit">Maximum file size: 10MB</p>
                                            </div>
                                        </div>
                                    </motion.div>

                                    <AnimatePresence>
                                        {error && (
                                            <motion.div
                                                id="error-message"
                                                className="status-message error"
                                                role="alert"
                                                aria-live="polite"
                                                initial={{ opacity: 0, x: -20, height: 0 }}
                                                animate={{ opacity: 1, x: 0, height: "auto" }}
                                                exit={{ opacity: 0, x: -20, height: 0 }}
                                                transition={{ duration: 0.3 }}
                                            >
                                                <span className="status-icon">⚠️</span>
                                                <span>{error}</span>
                                            </motion.div>
                                        )}

                                        {csvData && fileName && (
                                            <motion.div
                                                className="status-message success"
                                                role="status"
                                                aria-live="polite"
                                                initial={{ opacity: 0, x: -20, height: 0 }}
                                                animate={{ opacity: 1, x: 0, height: "auto" }}
                                                exit={{ opacity: 0, x: -20, height: 0 }}
                                                transition={{ duration: 0.3 }}
                                            >
                                                <span className="status-icon">✅</span>
                                                <span>
                                                    <strong>{fileName}</strong> uploaded successfully!
                                                </span>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <motion.div
                                        className="upload-actions"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.6, delay: 1.6 }}
                                    >
                                        <AnimatePresence>
                                            {csvData && (
                                                <motion.button
                                                    onClick={resetUpload}
                                                    className="btn btn-secondary"
                                                    type="button"
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    exit={{ opacity: 0, scale: 0.8 }}
                                                    whileHover={{ scale: 1.05, y: -2 }}
                                                    whileTap={{ scale: 0.95 }}
                                                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                                >
                                                    Upload New File
                                                </motion.button>
                                            )}
                                        </AnimatePresence>

                                        <motion.button
                                            onClick={handleProcessData}
                                            disabled={!csvData || isLoading || isProcessing}
                                            className={`btn btn-primary ${(isLoading || isProcessing) ? 'loading' : ''}`}
                                            type="button"
                                            whileHover={{ scale: !csvData || isLoading || isProcessing ? 1 : 1.05, y: !csvData || isLoading || isProcessing ? 0 : -2 }}
                                            whileTap={{ scale: !csvData || isLoading || isProcessing ? 1 : 0.95 }}
                                            transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                        >
                                            <AnimatePresence mode="wait">
                                                {isLoading ? (
                                                    <motion.div
                                                        key="loading"
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        exit={{ opacity: 0 }}
                                                        style={{ display: "flex", alignItems: "center", gap: "8px" }}
                                                    >
                                                        <div className="spinner"></div>
                                                        Reading File...
                                                    </motion.div>
                                                ) : isProcessing ? (
                                                    <motion.div
                                                        key="processing"
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        exit={{ opacity: 0 }}
                                                        style={{ display: "flex", alignItems: "center", gap: "8px" }}
                                                    >
                                                        <div className="spinner"></div>
                                                        Processing Data...
                                                    </motion.div>
                                                ) : (
                                                    <motion.div
                                                        key="default"
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        exit={{ opacity: 0 }}
                                                        style={{ display: "flex", alignItems: "center", gap: "8px" }}
                                                    >
                                                        Process Data
                                                        <span className="btn-arrow">→</span>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.button>
                                    </motion.div>
                                </motion.div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.section>

            {/* Results Section */}
            <AnimatePresence>
                {showResults && processedResults && (
                    <motion.section
                        className="results-section"
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -50 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="container">
                            <motion.div
                                className="results-card"
                                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.7, delay: 0.2 }}
                            >
                                <motion.div
                                    className="results-header"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.4 }}
                                >
                                    <div className="results-icon">✅</div>
                                    <h3 className="results-title">Processing Complete</h3>
                                    <p className="results-description">
                                        Your profile verification data has been processed successfully.
                                    </p>
                                </motion.div>

                                <motion.div
                                    className="results-summary"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.6 }}
                                >
                                    <div className="summary-stats">
                                        <div className="stat">
                                            <span className="stat-label">Total Rows</span>
                                            <span className="stat-value">{processedResults.summary.total_rows}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Valid Rows</span>
                                            <span className="stat-value">{processedResults.summary.valid_rows}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Invalid Rows</span>
                                            <span className="stat-value">{processedResults.summary.invalid_rows}</span>
                                        </div>
                                        <div className="stat">
                                            <span className="stat-label">Validation Rate</span>
                                            <span className="stat-value">{processedResults.summary.validation_rate.toFixed(1)}%</span>
                                        </div>
                                    </div>
                                </motion.div>

                                <motion.div
                                    className="results-actions"
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6, delay: 0.8 }}
                                >
                                    <motion.button
                                        onClick={downloadProcessedCSV}
                                        className="btn btn-primary"
                                        whileHover={{ scale: 1.05, y: -2 }}
                                        whileTap={{ scale: 0.95 }}
                                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                    >
                                        <span>📥</span>
                                        Download Processed CSV
                                    </motion.button>
                                    <motion.button
                                        onClick={resetUpload}
                                        className="btn btn-secondary"
                                        whileHover={{ scale: 1.05, y: -2 }}
                                        whileTap={{ scale: 0.95 }}
                                        transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                    >
                                        Process Another File
                                    </motion.button>
                                </motion.div>
                            </motion.div>
                        </div>
                    </motion.section>
                )}
            </AnimatePresence>

            {/* Features Section */}
            <motion.section
                className="features-section"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
            >
                <div className="container">
                    <motion.div
                        className="features-grid"
                        variants={staggerContainer}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, margin: "-50px" }}
                    >
                        <motion.div
                            className="feature-card"
                            variants={cardVariants}
                            whileHover={{ y: -10, scale: 1.02 }}
                            transition={{ type: "spring", stiffness: 300, damping: 20 }}
                        >
                            <motion.div
                                className="feature-icon"
                                initial={{ scale: 0, rotate: -180 }}
                                whileInView={{ scale: 1, rotate: 0 }}
                                viewport={{ once: true }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                            >
                                <span>🔍</span>
                            </motion.div>
                            <motion.h3
                                className="feature-title"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.3 }}
                            >
                                SOP Compliance
                            </motion.h3>
                            <motion.p
                                className="feature-description"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.4 }}
                            >
                                Validates verification details against Standard Operating Procedures
                            </motion.p>
                        </motion.div>

                        <motion.div
                            className="feature-card"
                            variants={cardVariants}
                            whileHover={{ y: -10, scale: 1.02 }}
                            transition={{ type: "spring", stiffness: 300, damping: 20 }}
                        >
                            <motion.div
                                className="feature-icon"
                                initial={{ scale: 0, rotate: -180 }}
                                whileInView={{ scale: 1, rotate: 0 }}
                                viewport={{ once: true }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.4 }}
                            >
                                <span>🛡️</span>
                            </motion.div>
                            <motion.h3
                                className="feature-title"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.5 }}
                            >
                                Data Integrity
                            </motion.h3>
                            <motion.p
                                className="feature-description"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.6 }}
                            >
                                Ensures accuracy and completeness of verification data
                            </motion.p>
                        </motion.div>

                        <motion.div
                            className="feature-card"
                            variants={cardVariants}
                            whileHover={{ y: -10, scale: 1.02 }}
                            transition={{ type: "spring", stiffness: 300, damping: 20 }}
                        >
                            <motion.div
                                className="feature-icon"
                                initial={{ scale: 0, rotate: -180 }}
                                whileInView={{ scale: 1, rotate: 0 }}
                                viewport={{ once: true }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.6 }}
                            >
                                <span>📊</span>
                            </motion.div>
                            <motion.h3
                                className="feature-title"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.7 }}
                            >
                                Smart Analysis
                            </motion.h3>
                            <motion.p
                                className="feature-description"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: 0.8 }}
                            >
                                Cross-checks entries with credible sources and validates claims
                            </motion.p>
                        </motion.div>
                    </motion.div>
                </div>
            </motion.section>

            {/* Trust Section */}
            <motion.section
                className="trust-section"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.6, delay: 0.2 }}
            >
                <div className="container">
                    <motion.p
                        className="trust-text"
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: 0.4 }}
                    >
                        <motion.span
                            className="trust-icon"
                            initial={{ scale: 0, rotate: -90 }}
                            whileInView={{ scale: 1, rotate: 0 }}
                            viewport={{ once: true }}
                            transition={{ type: "spring", stiffness: 300, delay: 0.6 }}
                        >
                            🔒
                        </motion.span>
                        Your data is processed securely and handled according to data governance protocols
                    </motion.p>
                </div>
            </motion.section>
        </motion.div>
    );
}