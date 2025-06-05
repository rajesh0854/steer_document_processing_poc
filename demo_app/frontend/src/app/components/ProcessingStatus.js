'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Grid,
  Paper,
  CircularProgress,
  Fade,
  Zoom,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  PictureAsPdf,
  Schema,
  AutoAwesome,
  Timer,
  CloudUpload,
  Psychology,
  DataObject,
  Verified,
} from '@mui/icons-material';

export default function ProcessingStatus({ 
  processing, 
  onProcess, 
  uploadedFile, 
  selectedSchema, 
  canProcess 
}) {
  const [processingStep, setProcessingStep] = useState(0);
  const [animationPhase, setAnimationPhase] = useState(0);
  const [processingSteps] = useState([
    { text: 'Initializing AI processing...', icon: <AutoAwesome /> },
    { text: 'Uploading PDFs to Gemini...', icon: <CloudUpload /> },
    { text: 'Analyzing document structure...', icon: <Psychology /> },
    { text: 'Extracting data fields...', icon: <DataObject /> },
    { text: 'Validating extracted data...', icon: <Verified /> },
    { text: 'Finalizing results...', icon: <CheckCircle /> },
  ]);

  useEffect(() => {
    let stepInterval;
    let phaseInterval;
    
    if (processing) {
      setProcessingStep(0);
      setAnimationPhase(0);
      
      // Change processing step every 3 seconds
      stepInterval = setInterval(() => {
        setProcessingStep(prev => {
          if (prev < processingSteps.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 3000);
      
      // Animation phase for visual effects
      phaseInterval = setInterval(() => {
        setAnimationPhase(prev => (prev + 1) % 4);
      }, 800);
    } else {
      setProcessingStep(0);
      setAnimationPhase(0);
    }

    return () => {
      if (stepInterval) clearInterval(stepInterval);
      if (phaseInterval) clearInterval(phaseInterval);
    };
  }, [processing, processingSteps.length]);

  const getProcessingProgress = () => {
    return ((processingStep + 1) / processingSteps.length) * 100;
  };

  if (processing) {
    return (
      <Box>
        <Typography variant="h5" gutterBottom align="center">
          Processing Documents
        </Typography>
        
        <Card sx={{ mb: 3, overflow: 'hidden', position: 'relative' }}>
          {/* Animated Background */}
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: `linear-gradient(45deg, 
                rgba(25, 118, 210, 0.05) 0%, 
                rgba(25, 118, 210, 0.1) 50%, 
                rgba(25, 118, 210, 0.05) 100%)`,
              animation: 'shimmer 3s ease-in-out infinite',
              '@keyframes shimmer': {
                '0%': { transform: 'translateX(-100%)' },
                '100%': { transform: 'translateX(100%)' },
              },
            }}
          />
          
          <CardContent sx={{ position: 'relative', zIndex: 1 }}>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              {/* Main Processing Icon with Rotation */}
              <Zoom in={true} timeout={1000}>
                <Box sx={{ position: 'relative', display: 'inline-block' }}>
                  <CircularProgress
                    size={80}
                    thickness={2}
                    sx={{
                      color: 'primary.main',
                      animation: 'spin 2s linear infinite',
                      '@keyframes spin': {
                        '0%': { transform: 'rotate(0deg)' },
                        '100%': { transform: 'rotate(360deg)' },
                      },
                    }}
                  />
                  <Box
                    sx={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      animation: 'pulse 2s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%, 100%': { transform: 'translate(-50%, -50%) scale(1)' },
                        '50%': { transform: 'translate(-50%, -50%) scale(1.1)' },
                      },
                    }}
                  >
                    {processingSteps[processingStep]?.icon}
                  </Box>
                </Box>
              </Zoom>
              
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                AI is extracting data from your documents
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This may take a few minutes depending on document complexity
              </Typography>
            </Box>

            {/* Current Step Display */}
            <Fade in={true} timeout={500} key={processingStep}>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                  <Box sx={{ mr: 2, color: 'primary.main' }}>
                    {processingSteps[processingStep]?.icon}
                  </Box>
                  <Typography variant="h6" color="primary">
                    {processingSteps[processingStep]?.text}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Step {processingStep + 1} of {processingSteps.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {Math.round(getProcessingProgress())}%
                  </Typography>
                </Box>
                
                <LinearProgress 
                  variant="determinate" 
                  value={getProcessingProgress()}
                  sx={{ 
                    height: 8, 
                    borderRadius: 4,
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 4,
                      background: 'linear-gradient(90deg, #1976d2 0%, #42a5f5 100%)',
                    },
                  }}
                />
              </Box>
            </Fade>

            {/* Processing Steps Timeline */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom align="center">
                Processing Timeline
              </Typography>
              <Grid container spacing={1} justifyContent="center">
                {processingSteps.map((step, index) => (
                  <Grid item key={index}>
                    <Chip
                      icon={step.icon}
                      label={`Step ${index + 1}`}
                      size="small"
                      color={index <= processingStep ? "primary" : "default"}
                      variant={index === processingStep ? "filled" : "outlined"}
                      sx={{
                        animation: index === processingStep ? 'glow 2s ease-in-out infinite' : 'none',
                        '@keyframes glow': {
                          '0%, 100%': { boxShadow: '0 0 5px rgba(25, 118, 210, 0.5)' },
                          '50%': { boxShadow: '0 0 20px rgba(25, 118, 210, 0.8)' },
                        },
                      }}
                    />
                  </Grid>
                ))}
              </Grid>
            </Box>

            {/* Stats Cards */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {uploadedFile ? 1 : 0}
                  </Typography>
                  <Typography variant="caption">
                    File Processing
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={6}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'secondary.light', color: 'white' }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {selectedSchema?.fields?.length || 0}
                  </Typography>
                  <Typography variant="caption">
                    Fields Extracting
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Please wait while we process your documents. Do not close this window.
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Ready to Process
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Review your settings and start the data extraction process
      </Typography>

      {/* Processing Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: 200 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PictureAsPdf color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Uploaded File
                </Typography>
              </Box>
              <Typography variant="h3" color="primary" gutterBottom sx={{ fontWeight: 'bold' }}>
                {uploadedFile ? 1 : 0}
              </Typography>
              <List dense>
                {uploadedFile && (
                  <ListItem sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <CheckCircle color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={uploadedFile.original_name}
                      primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: 200 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Schema color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Selected Schema
                </Typography>
              </Box>
              {selectedSchema ? (
                <>
                  <Typography variant="h6" color="primary" gutterBottom noWrap>
                    {selectedSchema.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {selectedSchema.description || 'No description'}
                  </Typography>
                  <Chip 
                    label={`${selectedSchema.fields?.length || 0} fields`}
                    color="primary"
                    size="small"
                  />
                </>
              ) : (
                <Typography variant="body2" color="error">
                  No schema selected
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: 200 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Timer color="action" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Estimated Time
                </Typography>
              </Box>
              <Typography variant="h3" color="primary" gutterBottom sx={{ fontWeight: 'bold' }}>
                {uploadedFile ? '2-4' : '0'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                minutes (approximate)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Validation Messages */}
      {!canProcess && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Cannot start processing:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {!uploadedFile && <li>No file uploaded</li>}
            {!selectedSchema && <li>No schema selected</li>}
          </ul>
        </Alert>
      )}

      {/* Schema Fields Preview */}
      {selectedSchema && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Fields to Extract
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The following data will be extracted from each document:
            </Typography>
            <Grid container spacing={1}>
              {selectedSchema.fields?.map((field, index) => (
                <Grid item key={index}>
                  <Chip
                    label={`${field.name} (${field.type})`}
                    variant="outlined"
                    size="small"
                    color={field.required ? "primary" : "default"}
                  />
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Process Button */}
      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={onProcess}
          disabled={!canProcess}
          startIcon={<PlayArrow />}
          sx={{ 
            minWidth: 250,
            py: 1.5,
            fontSize: '1.1rem',
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
            },
          }}
        >
          Start Processing
        </Button>
      </Box>

      {/* Processing Information */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          What happens during processing?
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.875rem' }}>
              <li>Direct PDF upload to Gemini AI</li>
              <li>AI-powered content analysis</li>
              <li>Field-specific data extraction</li>
            </ul>
          </Grid>
          <Grid item xs={12} md={6}>
            <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.875rem' }}>
              <li>Data validation and formatting</li>
              <li>Results compilation</li>
              <li>Export preparation</li>
            </ul>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
} 