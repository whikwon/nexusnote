import { useState, useRef, useEffect } from 'react';
import React from 'react';
import { Viewer, Worker, Button, Position, PrimaryButton, Tooltip } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import {
  highlightPlugin,
  HighlightArea,
  MessageIcon,
  RenderHighlightContentProps,
  RenderHighlightsProps,
  RenderHighlightTargetProps,
} from '@react-pdf-viewer/highlight';
import '@react-pdf-viewer/highlight/lib/styles/index.css';

import { searchPlugin } from '@react-pdf-viewer/search';
import { bookmarkPlugin } from '@react-pdf-viewer/bookmark';

import UpdateElectron from '@/components/update';
import './App.css';

import { thumbnailPlugin } from '@react-pdf-viewer/thumbnail';
import { toolbarPlugin, ToolbarSlot } from '@react-pdf-viewer/toolbar';
import '@react-pdf-viewer/thumbnail/lib/styles/index.css';
import '@react-pdf-viewer/toolbar/lib/styles/index.css';

// Dummy icon for the sidebar toggle. You can replace it with any icon component.
const MenuIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20">
    <rect x="2" y="4" width="16" height="2" fill="currentColor" />
    <rect x="2" y="9" width="16" height="2" fill="currentColor" />
    <rect x="2" y="14" width="16" height="2" fill="currentColor" />
  </svg>
);

// Add this custom UploadIcon component near the MenuIcon component
const UploadIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M11 14.9861C11 15.5384 11.4477 15.9861 12 15.9861C12.5523 15.9861 13 15.5384 13 14.9861V7.82831L16.2428 11.0711L17.657 9.65685L12 4L6.34315 9.65685L7.75736 11.0711L11 7.82831V14.9861Z"
      fill="currentColor"
    />
    <path
      d="M4 14H6V18H18V14H20V18C20 19.1046 19.1046 20 18 20H6C4.89543 20 4 19.1046 4 18V14Z"
      fill="currentColor"
    />
  </svg>
);

interface AnnotationBase {
  id: string;
  file_id: string;
  highlight_areas: HighlightArea[];
  created_at: string;
  updated_at: string;
  comment: string;
}

// Add this interface near other interfaces
interface ConceptCreate {
  name: string;
  annotation_ids?: number[];
  comment: string;
  linked_concept_ids?: number[];
}

function App() {
  // ===== Note related interfaces and state =====
  interface Note {
    id: string;
    file_id: string;
    comment: string;
    highlight_areas: HighlightArea[];
    quote: string;
  }

  const [message, setMessage] = useState('');
  const [notes, setNotes] = useState<Note[]>([]);
  const noteEles = useRef(new Map<string, HTMLElement>());

  // ===== Left sidebar state (Notes/Thumbnails/Bookmarks) =====
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [activeTab, setActiveTab] = useState<'notes' | 'thumbnails' | 'bookmarks'>('notes');

  // ===== Concept (Zettelkasten permanent note) related interfaces and state =====
  interface Concept {
    id: string;
    name: string;
    comment: string;
    annotation_ids: string[];
    linked_concept_ids: string[];
  }

  const [documentConcepts, setDocumentConcepts] = useState<Concept[]>([]);
  const [allConcepts, setAllConcepts] = useState<Concept[]>([]);
  const [activeConcept, setActiveConcept] = useState<Concept | null>(null);

  // Local state for concept creation and inputs
  const [newConceptTitle, setNewConceptTitle] = useState('');

  // For searching available notes and concepts when linking
  const [annotationSearchTerm, setAnnotationSearchTerm] = useState('');
  const [conceptSearchTerm, setConceptSearchTerm] = useState('');

  // ===== Helper function to truncate text =====
  const truncate = (text: string, max: number) => {
    return text.length > max ? text.substring(0, max) + '...' : text;
  };

  // ===== Highlight plugin functions =====
  const renderHighlightTarget = (props: RenderHighlightTargetProps) => (
    <div
      style={{
        background: '#eee',
        display: 'flex',
        position: 'absolute',
        left: `${props.selectionRegion.left}%`,
        top: `${props.selectionRegion.top + props.selectionRegion.height}%`,
        transform: 'translate(0, 8px)',
        zIndex: 1,
      }}
    >
      <Tooltip
        position={Position.TopCenter}
        target={
          <Button onClick={props.toggle}>
            <MessageIcon />
          </Button>
        }
        content={() => <div style={{ width: '100px' }}>Add a note</div>}
        offset={{ left: 0, top: -8 }}
      />
    </div>
  );

  const renderHighlightContent = (props: RenderHighlightContentProps) => {
    return (
      <div
        style={{
          background: '#fff',
          border: '1px solid rgba(0, 0, 0, .3)',
          borderRadius: '2px',
          padding: '8px',
          position: 'absolute',
          left: `${props.selectionRegion.left}%`,
          top: `${props.selectionRegion.top + props.selectionRegion.height}%`,
          zIndex: 1,
        }}
      >
        <div>
          <textarea
            rows={3}
            className="custom-textarea"
            value={message}
            onChange={e => setMessage(e.target.value)}
          ></textarea>
        </div>
        <div style={{ display: 'flex', fontSize: '1.0rem' }}>
          <div style={{ marginRight: '8px' }}>
            <PrimaryButton
              onClick={async () => {
                if (message !== '') {
                  try {
                    const response = await fetch('http://localhost:8000/api/v1/annotation/create', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        file_id: documentMetadata.id,
                        comment: message,
                        highlight_areas: props.highlightAreas,
                        quote: props.selectedText,
                      }),
                    });

                    if (!response.ok) {
                      throw new Error('Failed to create annotation');
                    }

                    const responseJson = await response.json();
                    console.log(responseJson);
                    const newNote: Note = {
                      id: responseJson.id,
                      file_id: responseJson.file_id,
                      comment: responseJson.comment,
                      highlight_areas: responseJson.highlight_areas,
                      quote: responseJson.quote,
                    };
                    console.log(newNote);
                    setNotes(prevNotes => [...prevNotes, newNote]);
                    setMessage('');
                    props.cancel();
                  } catch (error) {
                    console.error('Error creating annotation:', error);
                    alert('Failed to create annotation. Please try again.');
                  }
                }
              }}
            >
              Add
            </PrimaryButton>
          </div>
          <Button
            onClick={() => {
              setMessage('');
              props.cancel();
            }}
          >
            Cancel
          </Button>
        </div>
      </div>
    );
  };

  const jumpToNote = (note: Note) => {
    const noteElement = noteEles.current.get(note.id);
    if (noteElement) {
      noteElement.scrollIntoView();
    }
  };

  const renderHighlights = (props: RenderHighlightsProps) => (
    <div>
      {notes.map(note => (
        <React.Fragment key={note.id}>
          {note.highlight_areas
            .filter(area => area.pageIndex === props.pageIndex)
            .map((area, idx) => (
              <div
                key={idx}
                style={Object.assign(
                  {},
                  { background: 'yellow', opacity: 0.4 },
                  props.getCssProperties(area, props.rotation)
                )}
                onClick={() => jumpToNote(note)}
                ref={(ref): void => {
                  if (ref) noteEles.current.set(note.id, ref);
                }}
              />
            ))}
        </React.Fragment>
      ))}
    </div>
  );

  const highlightPluginInstance = highlightPlugin({
    renderHighlightTarget,
    renderHighlightContent,
    renderHighlights,
  });

  const searchPluginInstance = searchPlugin();
  const thumbnailPluginInstance = thumbnailPlugin();
  const toolbarPluginInstance = toolbarPlugin();
  const bookmarkPluginInstance = bookmarkPlugin();

  const { Bookmarks } = bookmarkPluginInstance;
  const { Thumbnails } = thumbnailPluginInstance;
  const { Toolbar } = toolbarPluginInstance;

  const deleteNote = async (id: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/annotation/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id }),
      });
      if (!response.ok) {
        throw new Error('Failed to delete annotation');
      }
      setNotes(prev => prev.filter(note => note.id !== id));
    } catch (error) {
      console.error('Error deleting note:', error);
      setMessage('Failed to delete note');
    }
  };

  // Toggle function for left sidebar visibility
  const toggleSidebar = () => {
    setSidebarVisible(prev => !prev);
  };

  // ===== Concept-related handlers =====

  // Update the handleAddConcept function
  const handleAddConcept = async () => {
    if (newConceptTitle.trim()) {
      try {
        // Prepare the concept data
        const newConcept: ConceptCreate = {
          name: newConceptTitle,
          annotation_ids: [],
          comment: '',
          linked_concept_ids: [],
        };

        // Make API request to create concept
        const response = await fetch('http://localhost:8000/api/v1/concept/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newConcept),
        });

        if (!response.ok) {
          throw new Error('Failed to create concept');
        }

        const createdConcept = await response.json();

        // Update local state
        setDocumentConcepts(prev => [...prev, createdConcept]);
        setAllConcepts(prev => [...prev, createdConcept]);
        setNewConceptTitle('');
      } catch (error) {
        console.error('Error creating concept:', error);
        // You might want to show an error message to the user here
      }
    }
  };

  // Set the active concept for viewing/editing
  const handleSelectConcept = (concept: Concept) => {
    setActiveConcept(concept);
    // Reset search terms when switching concepts
    setAnnotationSearchTerm('');
    setConceptSearchTerm('');
  };

  // Add a note annotation reference (by note id) to the active concept
  const addAnnotationRef = async (noteId: string) => {
    if (activeConcept && !activeConcept.annotation_ids.includes(noteId)) {
      const updatedConcept = {
        ...activeConcept,
        annotation_ids: [...activeConcept.annotation_ids, noteId],
      };
      try {
        const response = await fetch('http://localhost:8000/api/v1/concept/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedConcept),
        });
        if (!response.ok) {
          throw new Error('Failed to update annotation reference.');
        }
        const updatedConceptFromServer = await response.json();
        updateConcept(updatedConceptFromServer);
      } catch (error) {
        console.error('Error updating annotation reference:', error);
      }
    }
  };

  // Update the addLinkedConcept function to accept a string
  const addLinkedConcept = async (otherConceptId: string) => {
    if (
      activeConcept &&
      otherConceptId !== activeConcept.id &&
      !activeConcept.linked_concept_ids.includes(otherConceptId)
    ) {
      try {
        const payload = { concept_ids: [activeConcept.id, otherConceptId] };
        const response = await fetch('http://localhost:8000/api/v1/link/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error('Failed to create concept link');
        }
        const updatedConcept = {
          ...activeConcept,
          linked_concept_ids: [...activeConcept.linked_concept_ids, otherConceptId],
        };
        updateConcept(updatedConcept);
      } catch (error) {
        console.error('Error creating concept link:', error);
      }
    }
  };

  // Helper: update the concept in the state list and activeConcept if necessary
  const updateConcept = (updated: Concept) => {
    setDocumentConcepts(prev => prev.map(c => (c.id === updated.id ? updated : c)));
    setAllConcepts(prev => prev.map(c => (c.id === updated.id ? updated : c)));
    setActiveConcept(updated);
  };

  // New function to update concept comment on the backend
  const handleCommentSubmit = async () => {
    if (!activeConcept) return;
    try {
      const response = await fetch('http://localhost:8000/api/v1/concept/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(activeConcept),
      });
      if (!response.ok) {
        throw new Error('Failed to update concept comment.');
      }
      const updatedConcept = await response.json();
      setActiveConcept(updatedConcept);
      setDocumentConcepts(prev => prev.map(c => (c.id === updatedConcept.id ? updatedConcept : c)));
    } catch (error) {
      console.error('Error updating concept comment:', error);
      alert('Error updating concept comment.');
    }
  };

  // ===== Filtering functions for search-based linking =====
  const filteredNotes = notes.filter(n => {
    // Exclude notes already referenced
    if (activeConcept?.annotation_ids.includes(n.id)) return false;
    const term = annotationSearchTerm.toLowerCase();
    return n.quote.toLowerCase().includes(term) || n.comment.toLowerCase().includes(term);
  });

  const filteredConcepts = allConcepts.filter(c => {
    // Exclude the active concept and already linked ones
    if (
      activeConcept &&
      (c.id === activeConcept.id || activeConcept.linked_concept_ids.includes(c.id))
    )
      return false;
    const term = conceptSearchTerm.toLowerCase();
    return c.name.toLowerCase().includes(term);
  });

  // Add this state near other state declarations
  const [isUploading, setIsUploading] = useState(false);

  // Update the handleFileUpload function to use fetchDocument instead of fetchPDF
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/document/upload', {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      console.log('Upload successful:', data);

      // After successful upload, fetch and display the new PDF
      if (data.id) {
        await fetchDocument(data.id);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert(error instanceof Error ? error.message : 'Failed to upload PDF. Please try again.');
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  // Add these states near other state declarations
  const [pdfData, setPdfData] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add these states near other state declarations
  const [annotations, setAnnotations] = useState<AnnotationBase[]>([]);
  const [documentMetadata, setDocumentMetadata] = useState<DocumentBase | null>(null);

  // Update the fetchDocument function to properly handle the PDF data
  const fetchDocument = async (documentId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch PDF content and metadata in parallel
      const [pdfResponse, metadataResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/document/${documentId}`),
        fetch(`http://localhost:8000/api/v1/document/${documentId}/metadata`),
      ]);

      if (!pdfResponse.ok) {
        throw new Error(`HTTP error! status: ${pdfResponse.status}`);
      }
      if (!metadataResponse.ok) {
        throw new Error(`HTTP error! status: ${metadataResponse.status}`);
      }

      // Handle PDF content - create a blob URL instead of base64
      const blob = await pdfResponse.blob();
      const pdfUrl = URL.createObjectURL(blob);
      setPdfData(pdfUrl);

      // Handle metadata
      const metadata = await metadataResponse.json();
      console.log(metadata);
      setDocumentMetadata(metadata.document);
      setAnnotations(metadata.annotations);
      setNotes(metadata.annotations);
      setDocumentConcepts(metadata.concepts);

      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document');
      setIsLoading(false);
    }
  };

  // Add cleanup for blob URL when component unmounts
  useEffect(() => {
    return () => {
      // Cleanup blob URL when component unmounts
      if (pdfData) {
        URL.revokeObjectURL(pdfData);
      }
    };
  }, [pdfData]);

  // Update useEffect to use the new function name
  useEffect(() => {
    const documentId = '8ed2cc65-796b-4a62-ae12-4c9cdc9cf584';
    fetchDocument(documentId);
  }, []);

  useEffect(() => {
    const fetchConcepts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/concept/all');
        if (!response.ok) {
          throw new Error('Failed to fetch all concepts');
        }
        const data = await response.json();
        setAllConcepts(data);
        console.log(data);
      } catch (error) {
        console.error('Error fetching concepts:', error);
      }
    };

    fetchConcepts();
  }, []);

  // Helper function to return a concept's name by matching its id
  const getConceptName = (conceptId: string) => {
    console.log(allConcepts);
    const concept = allConcepts.find(c => c.id === conceptId);
    return concept ? concept.name : conceptId;
  };

  return (
    <div style={{ height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Worker workerUrl={new URL('pdfjs-dist/build/pdf.worker.js', import.meta.url).toString()}>
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Top Toolbar (with left sidebar toggle and PDF viewer toolbar) */}
          <div
            style={{
              padding: '8px',
              background: '#f1f1f1',
              borderBottom: '1px solid #ccc',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Button onClick={toggleSidebar} style={{ marginRight: '8px' }}>
              <MenuIcon />
            </Button>
            <Toolbar>
              {(props: ToolbarSlot) => {
                const {
                  CurrentPageInput,
                  Download,
                  EnterFullScreen,
                  GoToNextPage,
                  GoToPreviousPage,
                  NumberOfPages,
                  Print,
                  ShowSearchPopover,
                  Zoom,
                  ZoomIn,
                  ZoomOut,
                } = props;
                return (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      width: '100%',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <div style={{ position: 'relative' }}>
                        <Button onClick={() => document.getElementById('pdf-upload')?.click()}>
                          {isUploading ? <span>Uploading...</span> : <UploadIcon />}
                        </Button>
                        <input
                          type="file"
                          id="pdf-upload"
                          accept=".pdf"
                          onChange={handleFileUpload}
                          style={{
                            display: 'none',
                          }}
                        />
                      </div>
                      <ShowSearchPopover />
                      <ZoomOut />
                      <Zoom />
                      <ZoomIn />
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginLeft: 'auto',
                        gap: '8px',
                      }}
                    >
                      <GoToPreviousPage />
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <CurrentPageInput style={{ width: '3rem' }} />
                        / <NumberOfPages />
                      </div>
                      <GoToNextPage />
                      <EnterFullScreen />
                      <Download />
                      <Print />
                    </div>
                  </div>
                );
              }}
            </Toolbar>
          </div>
          {/* Main content area with left sidebar, PDF viewer, and right sidebar */}
          <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            {/* Left Sidebar: Notes/Thumbnails/Bookmarks */}
            {sidebarVisible && (
              <div
                style={{
                  width: '350px',
                  borderRight: '1px solid rgba(0,0,0,0.3)',
                  overflowY: 'auto',
                  padding: '10px',
                }}
              >
                <div style={{ display: 'flex', marginBottom: '10px' }}>
                  <Button
                    onClick={() => setActiveTab('notes')}
                    style={{
                      flex: 1,
                      background: activeTab === 'notes' ? '#ddd' : 'transparent',
                    }}
                  >
                    Notes
                  </Button>
                  <Button
                    onClick={() => setActiveTab('thumbnails')}
                    style={{
                      flex: 1,
                      background: activeTab === 'thumbnails' ? '#ddd' : 'transparent',
                    }}
                  >
                    Thumbnails
                  </Button>
                  <Button
                    onClick={() => setActiveTab('bookmarks')}
                    style={{
                      flex: 1,
                      background: activeTab === 'bookmarks' ? '#ddd' : 'transparent',
                    }}
                  >
                    Bookmarks
                  </Button>
                </div>
                {activeTab === 'notes' && (
                  <>
                    {notes.length === 0 && (
                      <div style={{ textAlign: 'center', padding: '8px' }}>There is no note</div>
                    )}
                    {notes.map(note => (
                      <div
                        key={note.id}
                        style={{
                          borderBottom: '1px solid rgba(0,0,0,0.3)',
                          cursor: 'pointer',
                          padding: '8px',
                          marginBottom: '8px',
                        }}
                      >
                        <div
                          onClick={() => {
                            if (note.highlightAreas.length > 0) {
                              highlightPluginInstance.jumpToHighlightArea(note.highlightAreas[0]);
                            }
                          }}
                          style={{ cursor: 'pointer' }}
                        >
                          <blockquote
                            style={{
                              borderLeft: '2px solid rgba(0,0,0,0.2)',
                              fontSize: '.75rem',
                              lineHeight: 1.5,
                              margin: '0 0 8px 0',
                              paddingLeft: '8px',
                              textAlign: 'justify',
                            }}
                          >
                            {note.quote}
                          </blockquote>
                          <div>{note.comment}</div>
                        </div>
                        <div
                          style={{
                            marginTop: '8px',
                            display: 'flex',
                            gap: '8px',
                          }}
                        >
                          <Button onClick={() => deleteNote(note.id)}>Delete</Button>
                        </div>
                      </div>
                    ))}
                  </>
                )}
                {activeTab === 'thumbnails' &&
                  (() => {
                    return <Thumbnails />;
                  })()}
                {activeTab === 'bookmarks' &&
                  (() => {
                    return <Bookmarks />;
                  })()}
              </div>
            )}

            {/* PDF Viewer */}
            <div style={{ flex: 1, height: '100%', overflow: 'auto' }}>
              {isLoading ? (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                  }}
                >
                  Loading PDF...
                </div>
              ) : error ? (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                    color: 'red',
                  }}
                >
                  Error: {error}
                </div>
              ) : (
                <Viewer
                  fileUrl={pdfData || ''}
                  plugins={[
                    highlightPluginInstance,
                    searchPluginInstance,
                    thumbnailPluginInstance,
                    toolbarPluginInstance,
                    bookmarkPluginInstance,
                  ]}
                />
              )}
            </div>

            {/* Right Sidebar: Concepts (Permanent Notes) */}
            <div
              style={{
                width: '300px',
                borderLeft: '1px solid rgba(0,0,0,0.3)',
                overflowY: 'auto',
                padding: '10px',
              }}
            >
              <h3>Concepts</h3>
              {/* New Concept Creation Form */}
              <div
                style={{
                  marginBottom: '16px',
                  borderBottom: '1px solid #ccc',
                  paddingBottom: '8px',
                }}
              >
                <input
                  type="text"
                  placeholder="Title"
                  value={newConceptTitle}
                  onChange={e => setNewConceptTitle(e.target.value)}
                  className="custom-input"
                  style={{ width: '100%', marginBottom: '4px' }}
                />
                <PrimaryButton onClick={handleAddConcept} style={{ width: '100%' }}>
                  Add Concept
                </PrimaryButton>
              </div>

              {/* List of Concepts */}
              <div style={{ marginBottom: '16px' }}>
                {documentConcepts.length === 0 ? (
                  <div style={{ textAlign: 'center' }}>No concepts yet</div>
                ) : (
                  documentConcepts.map(concept => (
                    <div
                      key={concept.id}
                      onClick={() => handleSelectConcept(concept)}
                      style={{
                        border: '1px solid #ccc',
                        padding: '8px',
                        marginBottom: '8px',
                        cursor: 'pointer',
                        background: activeConcept?.id === concept.id ? '#eef' : 'transparent',
                      }}
                    >
                      <strong>{concept.name}</strong>
                    </div>
                  ))
                )}
              </div>

              {/* Active Concept Details */}
              {activeConcept && (
                <div style={{ borderTop: '1px solid #ccc', paddingTop: '8px' }}>
                  {/* Annotation References Section */}
                  <div style={{ marginBottom: '16px' }}>
                    <strong>Annotation References:</strong>
                    {activeConcept.annotation_ids.length === 0 ? (
                      <p>No annotations referenced.</p>
                    ) : (
                      activeConcept.annotation_ids.map(refId => {
                        const note = notes.find(n => n.id === refId);
                        if (!note) return null;
                        return (
                          <div
                            key={refId}
                            style={{
                              border: '1px solid #ccc',
                              padding: '8px',
                              marginBottom: '8px',
                              borderRadius: '4px',
                              background: '#f9f9f9',
                            }}
                          >
                            <div>
                              <strong>Quote:</strong> {truncate(note.quote, 50)}
                            </div>
                            <div>
                              <strong>Comment:</strong> {truncate(note.comment, 100)}
                            </div>
                          </div>
                        );
                      })
                    )}
                    <input
                      type="text"
                      placeholder="Search notes..."
                      value={annotationSearchTerm}
                      onChange={e => setAnnotationSearchTerm(e.target.value)}
                      className="custom-input"
                      style={{ width: '100%', marginBottom: '4px' }}
                    />
                    {annotationSearchTerm && (
                      <div
                        style={{
                          maxHeight: '150px',
                          overflowY: 'auto',
                          border: '1px solid #ccc',
                          padding: '4px',
                        }}
                      >
                        {filteredNotes.length === 0 ? (
                          <div style={{ fontSize: '0.8rem', color: '#888' }}>No matching notes</div>
                        ) : (
                          filteredNotes.map(note => (
                            <div
                              key={note.id}
                              onClick={() => {
                                addAnnotationRef(note.id);
                                setAnnotationSearchTerm('');
                              }}
                              style={{
                                padding: '4px',
                                cursor: 'pointer',
                                borderBottom: '1px solid #eee',
                              }}
                            >
                              #{note.id}: {note.quote.slice(0, 30)}...
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>

                  {/* Comment Section */}
                  <div style={{ marginBottom: '16px' }}>
                    <strong style={{ marginBottom: '4px' }}>Concept Comment:</strong>
                    <textarea
                      rows={2}
                      placeholder="Add a comment"
                      className="custom-textarea"
                      value={activeConcept.comment}
                      onChange={e =>
                        setActiveConcept({
                          ...activeConcept,
                          comment: e.target.value,
                        })
                      }
                      style={{ width: '100%', marginTop: '16px' }}
                    />
                    <PrimaryButton onClick={handleCommentSubmit}>Submit Comment</PrimaryButton>
                  </div>

                  {/* Linked Concepts Section */}
                  <div>
                    <strong>Linked Concepts:</strong>
                    {activeConcept.linked_concept_ids.length === 0 ? (
                      <p>No linked concepts.</p>
                    ) : (
                      <ul>
                        {activeConcept.linked_concept_ids.map(linkId => {
                          const linkedConcept =
                            documentConcepts.find(c => c.id === linkId) ||
                            allConcepts.find(c => c.id === linkId);
                          return (
                            <li key={linkId}>
                              {linkedConcept ? linkedConcept.name : `Concept #${linkId}`}
                            </li>
                          );
                        })}
                      </ul>
                    )}
                    <input
                      type="text"
                      placeholder="Search concepts..."
                      value={conceptSearchTerm}
                      className="custom-input"
                      onChange={e => setConceptSearchTerm(e.target.value)}
                      style={{ width: '100%', marginBottom: '4px' }}
                    />
                    {conceptSearchTerm && (
                      <div
                        style={{
                          maxHeight: '150px',
                          overflowY: 'auto',
                          border: '1px solid #ccc',
                          padding: '4px',
                        }}
                      >
                        {filteredConcepts.length === 0 ? (
                          <div style={{ fontSize: '0.8rem', color: '#888' }}>
                            No matching concepts
                          </div>
                        ) : (
                          filteredConcepts.map(c => (
                            <div
                              key={c.id}
                              onClick={async () => {
                                await addLinkedConcept(c.id);
                                setConceptSearchTerm('');
                              }}
                              style={{
                                padding: '4px',
                                cursor: 'pointer',
                                borderBottom: '1px solid #eee',
                              }}
                            >
                              {c.name.slice(0, 30)}...
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Worker>
      <UpdateElectron />
    </div>
  );
}

export default App;
