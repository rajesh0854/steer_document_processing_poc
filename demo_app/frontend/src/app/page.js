'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import {
  CloudUpload,
  Schema,
  PlayArrow,
  GetApp,
  Refresh,
  Description,
} from '@mui/icons-material';
import toast from 'react-hot-toast';

import FileUpload from './components/FileUpload';
import SchemaManager from './components/SchemaManager';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsTable from './components/ResultsTable';
import { apiService } from './services/apiService';

const steps = ['Upload PDF', 'Select Schema', 'Process Document', 'View Results'];

export default function Home() {
  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [resultId, setResultId] = useState(null);

  const handleFileUpload = async (file) => {
    try {
      setProcessing(true);
      const response = await apiService.uploadFile(file);
      
      setUploadedFile(response.file);
      setSessionId(response.session_id);
      setActiveStep(1);
      
      toast.success('File uploaded successfully!');
    } catch (error) {
      toast.error(error.message || 'Failed to upload file');
    } finally {
      setProcessing(false);
    }
  };

  const handleSchemaSelect = (schema) => {
    setSelectedSchema(schema);
    setActiveStep(2);
    toast.success(`Schema "${schema.name}" selected`);
  };

  const handleProcessDocuments = async () => {
    if (!sessionId || !selectedSchema) {
      toast.error('Please upload files and select a schema first');
      return;
    }

    try {
      setProcessing(true);
      setActiveStep(2);
      
      const response = await apiService.processDocuments(sessionId, selectedSchema.id);
      
      setResults(response.results);
      setResultId(response.result_id);
      setActiveStep(3);
      
      toast.success('Documents processed successfully!');
    } catch (error) {
      toast.error(error.message || 'Failed to process documents');
    } finally {
      setProcessing(false);
    }
  };

  const handleExportResults = async () => {
    if (!resultId) {
      toast.error('No results to export');
      return;
    }

    try {
      await apiService.exportResults(resultId);
      toast.success('Results exported successfully!');
    } catch (error) {
      toast.error(error.message || 'Failed to export results');
    }
  };

  const handleReset = async () => {
    if (sessionId) {
      try {
        await apiService.resetSession(sessionId);
      } catch (error) {
        console.error('Failed to reset session:', error);
      }
    }

    setActiveStep(0);
    setUploadedFile(null);
    setSessionId(null);
    setSelectedSchema(null);
    setResults(null);
    setResultId(null);
    setProcessing(false);
    
    toast.success('Session reset successfully');
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <FileUpload
            onUpload={handleFileUpload}
            uploadedFile={uploadedFile}
            processing={processing}
          />
        );
      case 1:
        return (
          <SchemaManager
            onSchemaSelect={handleSchemaSelect}
            selectedSchema={selectedSchema}
          />
        );
      case 2:
        return (
          <ProcessingStatus
            processing={processing}
            onProcess={handleProcessDocuments}
            uploadedFile={uploadedFile}
            selectedSchema={selectedSchema}
            canProcess={!processing && sessionId && selectedSchema}
          />
        );
      case 3:
        return (
          <ResultsTable
            results={results}
            onExport={handleExportResults}
            processing={processing}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Description sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            PDF Data Extractor
          </Typography>
          <Button
            color="inherit"
            startIcon={<Refresh />}
            onClick={handleReset}
            disabled={processing}
          >
            Reset
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth={false} sx={{ py: 2, px: 3 }}>
        <Paper elevation={0} sx={{ p: 3, mb: 3, bgcolor: 'background.paper' }}>
          <Typography variant="h4" gutterBottom align="center" color="primary">
            Manufacturing Document Data Extraction
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 3 }}>
            Upload your quotation and enquiry PDF, define extraction schema, and get structured data
          </Typography>

          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel
                  StepIconProps={{
                    style: {
                      color: index <= activeStep ? '#1976d2' : '#ccc',
                    },
                  }}
                >
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>

        <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.paper' }}>
          {getStepContent(activeStep)}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button
            disabled={activeStep === 0 || processing}
            onClick={() => setActiveStep(activeStep - 1)}
            variant="outlined"
          >
            Back
          </Button>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            {activeStep === 2 && (
              <Button
                variant="contained"
                onClick={handleProcessDocuments}
                disabled={!sessionId || !selectedSchema || processing}
                startIcon={processing ? <div className="loading-spinner" /> : <PlayArrow />}
              >
                {processing ? 'Processing...' : 'Process Document'}
              </Button>
            )}
            
            {activeStep === 3 && results && (
              <Button
                variant="contained"
                onClick={handleExportResults}
                startIcon={<GetApp />}
                color="secondary"
              >
                Export to Excel
              </Button>
            )}
          </Box>
        </Box>

        {/* Summary Cards */}
        {(uploadedFile || selectedSchema || results) && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            {uploadedFile && (
              <Grid item xs={12} md={4}>
                <Card className="hover-card" sx={{ height: 100 }}>
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Uploaded File
                    </Typography>
                    <Typography variant="h4" color="primary">
                      1
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      PDF document ready
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
            
            {selectedSchema && (
              <Grid item xs={12} md={4}>
                <Card className="hover-card" sx={{ height: 100 }}>
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Selected Schema
                    </Typography>
                    <Typography variant="h6" color="primary" noWrap>
                      {selectedSchema.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {selectedSchema.fields?.length || 0} fields defined
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
            
            {results && (
              <Grid item xs={12} md={4}>
                <Card className="hover-card" sx={{ height: 100 }}>
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Processing Results
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {results.filter(r => r.status === 'success').length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Successfully processed
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}
      </Container>
    </Box>
  );
} 