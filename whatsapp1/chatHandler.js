const { OpenAI } = require('openai');
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const { getInvoiceLink, getUniqueNumber, getValidBLs, getInvoiceInfo, getPaymentStatus } = require('./db');
const { pool } = require('./db');
const { logMessage } = require('./logger');
const { generateReceiptPDF, uploadReceiptToCloudinary, updateBLStatusAndReceipt } = require('./receipt_utils');
const fetch = require('node-fetch');
const fs = require('fs');

// Import balance utilities for duplicate payment protection
const { checkPaymentProcessed, markPaymentProcessed, processPaymentBalance, getCustomerEmail, getCustomerUsername, getOriginalPaymentDate } = require('./utils/balance_utils_node');

// Import duplicate payment notifications
const { sendDuplicatePaymentNotifications } = require('./utils/duplicate_payment_notifications');

const conversationHistory = {};

// Enhanced SYSTEM_PROMPT with better handling for various question types
const SYSTEM_PROMPT = `You are a logistics assistant specializing in Cargo Tracking Note (CTN) processing. Respond in this JSON format:
{
  "intent": "request_invoice|ask_ctn_number|ask_payment_methods|ask_pricing|general_question|payment_receipt|other|ask_payment_status|out_of_scope|missing_context|technical_issue",
  "bl_number": "<BL number if present from context, else null>",
  "answer": "<Response based on intent and context>"
}

**IMPORTANT SCOPE CLARIFICATION:**
- We ONLY handle CTN (Cargo Tracking Note) processing and related fees
- We do NOT handle general shipment tracking, delivery status, or shipping carrier information
- For shipment tracking questions, redirect to shipping carriers

**Intent Classification Rules:**
- For 'request_invoice', 'ask_ctn_number', 'ask_payment_status', or 'payment_receipt' with invalid BLs [INVALID_BLS], return 'Sorry, the BL number(s) [INVALID_BLS] could not be found in our system. Please check and try again.'
- For 'ask_pricing', use this intent when customers ask about pricing, costs, fees, or payment amounts. This includes phrases like:
  * "how much do i need to pay for my invoice"
  * "what is the cost"
  * "how much does it cost"
  * "what are the fees"
  * "ctn fee and service fee"
  * "pricing"
  * "cost"
  * "amount to pay"
  * "invoice amount"
  * "payment amount"
- For 'out_of_scope', use for questions clearly outside CTN scope (weather, flights, general shipping, etc.)
- For 'missing_context', use for CTN-related questions that need BL numbers but don't provide them
- For 'technical_issue', use for technical problems the bot cannot resolve
- For 'general_question', match the query against these phrases and return the corresponding canned response if a partial match is found (e.g., key terms like "ctn" and "processing" for "ctn processing time"):
  - 'ctn processing time' → 'The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used. Let us know if you have further questions.'
  - 'payment methods' → 'We accept the following payment methods:\n- Bank Transfer\n- Allinpay\n- Stripe\nChoose the most convenient option. Instructions are provided when you generate a payment link.'
  - 'fees' → 'Our current fee structure is:\n- CTN Fee: $100 per container\n- Service Fee: $100 per container\nTotal: $200 per container. Contact us for details.'
  - 'how do i get a copy of my invoice' → 'Request a copy of your invoice by replying here or logging into our portal. Provide your B/L or CTN number if you need assistance.'
  - 'how do i track the status of my ctn' → 'To check your CTN status, provide your B/L or CTN number, and we'll update you soon.'
  - 'what documents do i need to provide for ctn processing' → 'For CTN processing, provide:\n- Bill of Lading (B/L)\n- Commercial Invoice\n- Packing List\n- Any other relevant shipping documents\nNo action needed if already submitted.'
  - 'how do i upload my bank transfer receipt' → 'Upload your bank transfer receipt by replying with it attached. We'll process it upon receipt.'
  - 'can i get a refund or cancel my ctn' → 'Refunds or cancellations are case-by-case. Provide your B/L or CTN number and reason for review.'
  - 'what is the difference between ctn and b l' → 'A Bill of Lading (B/L) is required to initiate CTN processing; a CTN is the note issued to track your cargo documentation status.'
  - 'what are your business hours' → 'We're open Monday to Friday, 9:00 AM to 6:00 PM (local time). Responses within one business day.'
  - 'how do i contact support' → 'Contact support by replying here or calling [your phone number]. We're here to help!'
  - 'can i pay in a different currency' → 'We accept USD only. Contact us in advance to discuss other currency options.'
  - 'how do i update my company contact information' → 'Update your company or contact info by replying with new details or via our online portal.'
  - 'how do i check my payment status' → 'To check your payment status, provide your BL number. We will update you on the current status of your payment after verification.'
  - 'how do i request urgent processing' → 'For urgent processing, please mention your BL number and the reason for urgency. We will prioritize your request if possible.'
  - If no sufficient match, return 'For general enquiries, please provide your BL number or contact support for assistance.'
- For other intents, provide a relevant response based on the context.
- Context: Valid BLs are [VALID_BLS], invalid BLs are [INVALID_BLS]. Available general enquiry phrases are: ctn processing time, payment methods, fees, how do i get a copy of my invoice, how do i track the status of my ctn, what documents do i need to provide for ctn processing, how do i upload my bank transfer receipt, can i get a refund or cancel my ctn, what is the difference between ctn and b l, what are your business hours, how do i contact support, can i pay in a different currency, how do i update my company contact information, how do i check my payment status, how do i request urgent processing.`;

// Enhanced CANNED_RESPONSES with comprehensive coverage
const CANNED_RESPONSES = {
  // Existing CTN-related responses
  'ctn processing time': 'The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used. Let us know if you have further questions.',
  'payment methods': 'We accept the following payment methods:\n- Bank Transfer\n- Allinpay\n- Stripe\nChoose the most convenient option. Instructions are provided when you generate a payment link.',
  'fees': 'Our current fee structure is:\n- CTN Fee: $100 per container\n- Service Fee: $100 per container\nTotal: $200 per container. Contact us for details.',
  'how do i get a copy of my invoice': 'Request a copy of your invoice by replying here or logging into our portal. Provide your B/L or CTN number if you need assistance.',
  'how do i track the status of my ctn': 'To check your CTN status, provide your B/L or CTN number, and we\'ll update you soon.',
  'what documents do i need to provide for ctn processing': 'For CTN processing, provide:\n- Bill of Lading (B/L)\n- Commercial Invoice\n- Packing List\n- Any other relevant shipping documents\nNo action needed if already submitted.',
  'how do i upload my bank transfer receipt': 'Upload your bank transfer receipt by replying with it attached. We\'ll process it upon receipt.',
  'can i get a refund or cancel my ctn': 'Refunds or cancellations are case-by-case. Provide your B/L or CTN number and reason for review.',
  'what is the difference between ctn and b l': 'A Bill of Lading (B/L) is required to initiate CTN processing; a CTN is the note issued to track your cargo documentation status.',
  'what are your business hours': 'We\'re open Monday to Friday, 9:00 AM to 6:00 PM (local time). Responses within one business day.',
  'how do i contact support': 'Contact support by replying here or calling [your phone number]. We\'re here to help!',
  'can i pay in a different currency': 'We accept USD only. Contact us in advance to discuss other currency options.',
  'how do i update my company contact information': 'Update your company or contact info by replying with new details or via our online portal.',
  'how do i check my payment status': 'To check your payment status, provide your BL number. We will update you on the current status of your payment after verification.',
  'how do i request urgent processing': 'For urgent processing, please mention your BL number and the reason for urgency. We will prioritize your request if possible.',
  
  // NEW: Missing context responses (CTN-related but need BL numbers)
  'how much do i owe': 'To check what you owe, please provide your BL number. I can then give you the exact amount for your CTN processing fees.',
  'where is my invoice': 'To locate your invoice, please provide your BL number. I can then provide you with the correct invoice link.',
  'when will i get my ctn': 'To check your CTN status, please provide your BL number. I can then tell you the current status of your CTN processing.',
  'whats the cost': 'To provide you with the exact cost, please provide your BL number. I can then give you the specific fees for your CTN processing.',
  'what documents do i need': 'To provide specific document requirements, please provide your BL number. I can then tell you exactly what documents are needed for your CTN processing.',
  'whats the status': 'To check the status, please provide your BL number. I can then give you the current status of your CTN processing.',
  'is it ready': 'To check if your CTN is ready, please provide your BL number. I can then tell you the current status.',
  'where is it': 'To check the status of your CTN, please provide your BL number. I can then give you the current information.',
  
  // NEW: Out-of-scope responses (clearly not CTN-related)
  'where is my shipment': 'We handle CTN processing, not shipment tracking. Please contact your shipping carrier for shipment status.',
  'when will it arrive': 'We handle CTN processing, not delivery tracking. Please contact your shipping carrier.',
  'whats my tracking number': 'We handle CTN processing. For shipment tracking, please contact your shipping carrier.',
  'whats the weather like': 'We handle CTN processing. For weather information, please check a weather service.',
  'can you book a flight': 'We handle CTN processing. For flight bookings, please contact a travel agency.',
  'how are you today': 'I\'m here to help with CTN processing. How can I assist you with your cargo tracking note?',
  'do you speak chinese': 'Yes, I can communicate in Chinese. How can I help you with your CTN processing?',
  'what time is it': 'I\'m here to help with CTN processing. For the current time, please check your device.',
  
  // NEW: Technical issue responses
  'the website is not working': 'If you\'re experiencing technical issues with our website, please try refreshing the page or contact our technical support team directly.',
  'i cant upload my receipt': 'If you\'re having trouble uploading your receipt, please try sending it as a photo or PDF attachment. If the issue persists, contact our support team.',
  'the payment link is broken': 'If you\'re experiencing issues with the payment link, please contact our support team immediately. We\'ll provide you with an alternative payment method.',
  'im getting an error message': 'If you\'re receiving an error message, please share the exact error text with our support team. We\'ll help you resolve the issue.',
  
  // NEW: Security-related responses
  'whats my password': 'For security reasons, I cannot provide password information. Please use the password reset function on our website or contact support.',
  'can you reset my account': 'For account security, please contact our support team directly. They will guide you through the account reset process.',
  'whats my credit card number': 'For security reasons, I cannot access or provide credit card information. Please contact your bank or payment provider directly.',
  
  // NEW: General clarification responses
  'what do you do': 'We specialize in Cargo Tracking Note (CTN) processing. We help you process the required documentation for your cargo shipments, including fee calculation, invoice generation, and payment processing.',
  'how does this work': 'CTN processing works as follows:\n1. You provide your Bill of Lading (B/L) number\n2. We calculate the required fees\n3. You make the payment\n4. We process your CTN documentation\n5. You receive your CTN number\n\nHow can I help you with your CTN processing?',
  'what is a ctn': 'A Cargo Tracking Note (CTN) is a mandatory document required for cargo shipments. It tracks the documentation status of your cargo and is processed based on your Bill of Lading (B/L). We handle the entire CTN processing workflow for you.'
};

// NEW: Out-of-scope question patterns (clearly not CTN-related)
const OUT_OF_SCOPE_PATTERNS = [
  /where\s+(is|are)\s+(my\s+)?shipment/i,
  /when\s+will\s+(it|my\s+shipment)\s+arrive/i,
  /whats?\s+my\s+tracking\s+number/i,
  /track\s+my\s+shipment/i,
  /shipment\s+status/i,
  /delivery\s+status/i,
  /whats?\s+the\s+weather/i,
  /can\s+you\s+book\s+a\s+flight/i,
  /weather\s+like/i,
  /book\s+flight/i,
  /flight\s+booking/i,
  /how\s+are\s+you\s+today/i,
  /what\s+time\s+is\s+it/i,
  /current\s+time/i
];

// NEW: Missing context patterns (CTN-related but need BL numbers)
const MISSING_CONTEXT_PATTERNS = [
  /how\s+much\s+(do\s+i\s+)?owe/i,
  /when\s+will\s+i\s+get\s+my\s+ctn/i,
  /whats?\s+the\s+cost/i,
  /what\s+documents\s+do\s+i\s+need/i,
  /whats?\s+the\s+status/i,
  /is\s+it\s+ready/i,
  /where\s+is\s+it/i,
  /how\s+much\s+(does\s+it\s+)?cost/i,
  /what\s+are\s+the\s+fees/i,
  /invoice\s+amount/i,
  /payment\s+amount/i
];

// NEW: Technical issue patterns
const TECHNICAL_ISSUE_PATTERNS = [
  /website\s+(is\s+)?not\s+working/i,
  /cant\s+upload/i,
  /payment\s+link\s+(is\s+)?broken/i,
  /getting\s+an?\s+error/i,
  /error\s+message/i,
  /technical\s+problem/i,
  /system\s+error/i,
  /page\s+not\s+loading/i
];

// NEW: Security-related patterns
const SECURITY_PATTERNS = [
  /whats?\s+my\s+password/i,
  /reset\s+my\s+account/i,
  /whats?\s+my\s+credit\s+card/i,
  /credit\s+card\s+number/i,
  /account\s+password/i,
  /login\s+credentials/i
];

function isEmail(str) { return typeof str === 'string' && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(str.trim()); }
function isChinese(text) { if (!text) return false; const chineseChars = Array.from(text).filter(c => /[\u4e00-\u9fff]/.test(c)).length; return chineseChars > 0 && chineseChars / Math.max(1, text.length) > 0.2; }
function extractBLNumbers(text) {
  if (!text) return [];
  
  // First, split by common separators and clean up
  const parts = text.split(/[,\s]+/).map(part => part.trim()).filter(part => part.length > 0);
  
  let allMatches = [];
  
  // Pattern 1: Standard BL patterns
  const blPattern = /(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})(?![^@]*@)/gi;
  let match;
  while ((match = blPattern.exec(text)) !== null) {
    if (match[1] && !match[1].includes('@')) {
      allMatches.push(match[1]);
    }
  }
  
  // Pattern 2: B/L format
  const blFormatPattern = /B\/L\s+([A-Z0-9\-]+)/gi;
  while ((match = blFormatPattern.exec(text)) !== null) {
    if (match[1] && !match[1].includes('@')) {
      allMatches.push(match[1]);
    }
  }
  
  // Pattern 3: Check individual parts for BL-like patterns
  for (const part of parts) {
    // Match patterns like NYC220, 001-123, etc.
    if (/^[A-Z]{2,4}\d{2,}$|^\d{3}-\d{3}$|^\d{4,}$/.test(part) && !part.includes('@')) {
      allMatches.push(part);
    }
  }
  
  // Filter out common bank reference patterns
  const bankRefPatterns = ['TEST', 'REF', 'BANK', 'PAY', 'TRANS', 'TXN', 'EST'];
  const filteredMatches = allMatches.filter(bl => {
    const blUpper = bl.toUpperCase();
    // Check if BL starts with bank reference prefixes
    if (bankRefPatterns.some(prefix => blUpper.startsWith(prefix))) {
      return false;
    }
    // Also check if BL contains bank reference patterns anywhere in the string
    if (bankRefPatterns.some(pattern => blUpper.includes(pattern))) {
      return false;
    }
    return true;
  });
  
  return Array.from(new Set(filteredMatches));
}
function extractPaymentAmount(text) { if (!text) return null; const patterns = [/\$\s?([0-9]+(?:\.[0-9]{1,2})?)/i, /USD\s*([0-9]+(?:\.[0-9]{1,2})?)/i, /Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)/i, /Paid[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)/i]; for (const pat of patterns) { const match = text.match(pat); if (match) try { return parseFloat(match[1]); } catch (e) { continue; } } return null; }

async function callOpenAI(messages) {
  try {
    return await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: messages,
    });
  } catch (error) {
    console.warn('GPT-3.5-turbo error, falling back to default response...');
    throw error;
  }
}

async function openaiTranslate(text, sourceLang, targetLang) {
  try {
    const translationPrompt = `Translate the following ${sourceLang} text to ${targetLang}. Only return the translated text, no explanation.\n\n${text}`;
    const response = await callOpenAI([{ role: 'system', content: 'You are a professional translator.' }, { role: 'user', content: translationPrompt }]);
    return response.choices[0].message.content.trim();
  } catch (e) {
    console.error('[OpenAI Translate] Failed:', e);
    return text;
  }
}

async function getIntentAndResponse(message, history, validBLs, invalidBLs) {
  const context = `Valid BLs are ${validBLs.join(', ') || 'none'}, invalid BLs are ${invalidBLs.join(', ') || 'none'}.`;
  const messages = [{ role: 'system', content: SYSTEM_PROMPT.replace('[VALID_BLS]', validBLs.join(', ') || 'none').replace('[INVALID_BLS]', invalidBLs.join(', ') || 'none') }, ...history];
  try {
    const completion = await callOpenAI(messages, { max_tokens: 300 });
    const content = completion.choices[0].message.content.trim();
    let result = {};
    try { result = JSON.parse(content.replace(/```json\n|\n```/g, '')); } catch (e) { result = { intent: 'general_question', bl_number: null, answer: content }; }
    console.log('[OpenAI JSON Response]:', JSON.stringify(result, null, 2));
    return result;
  } catch (e) { console.error('[OpenAI Error]:', e); return { intent: 'general_question', bl_number: null, answer: 'Sorry, an unexpected error occurred.' }; }
}

async function verifySensitiveAccess({ email, bl_number }) {
  try {
    const res = await fetch(`${process.env.FRONTEND_URL || 'https://iqstrade.onrender.com'}/api/verify_sensitive_access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, bl_number })
    });
    const data = await res.json(); // Parse JSON directly
    console.log('[DEBUG] Verification Response:', data); // Log the parsed response
    if (!res.ok) {
      throw new Error(data.message || 'Verification request failed');
    }
    return data;
  } catch (e) {
    console.error('[Verification Error]:', e.message);
    return { success: false, message: e.message || 'Error during verification' };
  }
}

async function chatHandler(message, sender, context = {}) {
  if (context.messages && context.messages[0]?.key?.fromMe) return '';

  if (!conversationHistory[sender]) conversationHistory[sender] = { history: [], session: { verifiedEmail: null, lastSentMsg: null, pendingResponse: null, pendingBLs: [], verificationTimestamp: null, lastValidatedBLs: [] } };
  conversationHistory[sender].history.push({ role: 'user', content: message || '' }); // Ensure message is defined

  const incomingIsChinese = isChinese(message);
  let blNumbers = extractBLNumbers(message || ''); // Extract BL numbers from current message
  console.log('[DEBUG] Extracted BL numbers from message:', blNumbers); // Debug extracted BLs
  let paidAmount = extractPaymentAmount(message) || (context.paid_amount || null);
  
  // If we have PDF content, also extract payment from that
  if (context.has_pdf && context.raw_text) {
    const pdfAmount = extractPaymentAmount(context.raw_text);
    if (pdfAmount && !paidAmount) {
      paidAmount = pdfAmount;
      console.log('[DEBUG] Using payment amount from PDF raw text:', pdfAmount);
    }
  }
  
  console.log('[DEBUG] Payment amount from text:', extractPaymentAmount(message), 'from context:', context.paid_amount, 'from PDF raw text:', context.has_pdf ? extractPaymentAmount(context.raw_text) : 'N/A', 'final:', paidAmount);
  let userEmail = conversationHistory[sender].session.verifiedEmail || context.email;
  let justProvidedEmail = isEmail(message) ? message.trim() : null;

  // Prioritize BLs from context if present
  if (context.bl_numbers && !context.skipBLExtraction) {
    blNumbers = Array.from(new Set([...context.bl_numbers, ...blNumbers])); // Context BLs first
    console.log('[DEBUG] Combined BL numbers from text and context:', blNumbers);
    conversationHistory[sender].history = conversationHistory[sender].history.filter(h => !h.content.startsWith('Untitled')); // Clear previous PDF context
  }
  
  // If we have PDF content in the message itself, extract BLs from that too
  if (context.has_pdf && context.raw_text) {
    const pdfBLs = extractBLNumbers(context.raw_text);
    blNumbers = Array.from(new Set([...blNumbers, ...pdfBLs]));
    console.log('[DEBUG] Added BLs from PDF raw text:', pdfBLs);
  }

  // Store and update last validated BLs only when new BLs are provided and validated
  if (blNumbers.length > 0) {
    // Ensure BL numbers are individual strings, not concatenated
    const cleanBLNumbers = blNumbers.filter(bl => typeof bl === 'string' && !bl.includes(',') && !bl.includes(' '));
    console.log('[DEBUG] Cleaned BL numbers:', cleanBLNumbers);
    
    const validBLs = await getValidBLs(cleanBLNumbers);
    if (validBLs.length > 0) {
      conversationHistory[sender].session.lastValidatedBLs = validBLs; // Update last validated BLs
    }
    blNumbers = validBLs; // Use validated BLs for current request
  } else {
    blNumbers = conversationHistory[sender].session.lastValidatedBLs; // Fallback to last validated BLs
  }

  // Store BLs from the initial request if verification is pending
  if (blNumbers.length > 0 && !conversationHistory[sender].session.verifiedEmail && !justProvidedEmail) {
    conversationHistory[sender].session.pendingBLs = blNumbers;
    // Store the last sensitive user request for replay after verification
    conversationHistory[sender].session.lastSensitiveRequest = message;
    console.log('[DEBUG] Stored pending BLs:', blNumbers);
  } else if (blNumbers.length > 0 && conversationHistory[sender].session.lastSensitiveRequest && !justProvidedEmail) {
    // Update pendingBLs with new BL provided after initial request, excluding email messages
    conversationHistory[sender].session.pendingBLs = Array.from(new Set([...conversationHistory[sender].session.pendingBLs, ...blNumbers]));
    console.log('[DEBUG] Updated pending BLs with new input:', conversationHistory[sender].session.pendingBLs);
  } else if (blNumbers.length > 0 && conversationHistory[sender].session.verifiedEmail) {
    // If user is already verified, use the BLs directly for processing
    conversationHistory[sender].session.pendingBLs = blNumbers;
    console.log('[DEBUG] User verified, using BLs directly:', blNumbers);
  }

  // Determine valid BLs without re-validating existing ones
  let validBLs = blNumbers.length > 0 ? blNumbers : [];
  if (blNumbers.length > 0 && blNumbers.some(bl => !conversationHistory[sender].session.lastValidatedBLs.includes(bl))) {
    const newValidBLs = await getValidBLs(blNumbers);
    validBLs = newValidBLs;
    if (newValidBLs.length > 0) {
      conversationHistory[sender].session.lastValidatedBLs = Array.from(new Set([...conversationHistory[sender].session.lastValidatedBLs, ...newValidBLs]));
    }
  }
  console.log('[DEBUG] Valid BLs from DB:', validBLs); // Debug valid BLs
  const invalidBLs = blNumbers.filter(bl => !validBLs.includes(bl));
  console.log('[DEBUG] Invalid BLs detected:', invalidBLs);
  console.log('[DEBUG] Final validBLs array type:', typeof validBLs, 'length:', validBLs.length, 'content:', JSON.stringify(validBLs));

  let intent = 'general_question'; // Default intent
  let blNumber = null;
  let answer = 'For general enquiries, please provide your BL number or contact support for assistance.';

  // NEW: Enhanced question detection logic
  const lowerMsg = (message || '').toLowerCase().replace(/[^-\w\s]/g, '');
  
  // Initialize variables for all code paths
  let isOutOfScope = false;
  let isTechnicalIssue = false;
  let isSecurityQuestion = false;
  let isMissingContext = false;
  
  // SPECIAL HANDLING: Direct invoice requests should trigger request_invoice intent
  if (/can\s+i\s+have\s+(my\s+)?invoice/i.test(message) || /can\s+you\s+send\s+(me\s+)?(my\s+)?invoice/i.test(message)) {
    intent = 'request_invoice';
    console.log('[DEBUG] Direct invoice request detected, setting intent to request_invoice');
  } else if (/can\s+i\s+have\s+(my\s+)?ctn\s+number/i.test(message) || /can\s+you\s+send\s+(me\s+)?(my\s+)?ctn\s+number/i.test(message) || /what\s+is\s+my\s+ctn\s+number/i.test(message)) {
    intent = 'ask_ctn_number';
    console.log('[DEBUG] Direct CTN number request detected, setting intent to ask_ctn_number');
  } else if (/can\s+i\s+check\s+(my\s+)?payment\s+status/i.test(message) || /what\s+is\s+my\s+payment\s+status/i.test(message) || /check\s+payment\s+status/i.test(message)) {
    intent = 'ask_payment_status';
    console.log('[DEBUG] Direct payment status request detected, setting intent to ask_payment_status');
  } else {
    // Check for out-of-scope questions first (clearly not CTN-related)
    for (const pattern of OUT_OF_SCOPE_PATTERNS) {
      if (pattern.test(message)) {
        isOutOfScope = true;
        intent = 'out_of_scope';
        break;
      }
    }
    
    // Check for technical issues
    if (!isOutOfScope) {
      for (const pattern of TECHNICAL_ISSUE_PATTERNS) {
        if (pattern.test(message)) {
          isTechnicalIssue = true;
          intent = 'technical_issue';
          break;
        }
      }
    }
    
    // Check for security-related questions
    if (!isOutOfScope && !isTechnicalIssue) {
      for (const pattern of SECURITY_PATTERNS) {
        if (pattern.test(message)) {
          isSecurityQuestion = true;
          intent = 'security_question';
          break;
        }
      }
    }
    
    // Check for missing context questions (CTN-related but need BL numbers)
    if (!isOutOfScope && !isTechnicalIssue && !isSecurityQuestion) {
      const blNumbersInMessage = extractBLNumbers(message);
      for (const pattern of MISSING_CONTEXT_PATTERNS) {
        if (pattern.test(message) && validBLs.length === 0 && blNumbersInMessage.length === 0) {
          isMissingContext = true;
          intent = 'missing_context';
          break;
        }
      }
    }

    // Pre-check for canned responses with partial matching (only if not already classified)
    if (!isOutOfScope && !isTechnicalIssue && !isSecurityQuestion && !isMissingContext) {
      const cannedKeys = Object.keys(CANNED_RESPONSES);
      let bestMatch = null;
      let highestSimilarity = 0;
      for (const key of cannedKeys) {
        const normalizedKey = key.replace(/[^-\w\s]/g, '');
        if (lowerMsg.includes(normalizedKey)) {
          const similarity = calculateSimilarity(lowerMsg, normalizedKey);
          if (similarity > highestSimilarity) {
            highestSimilarity = similarity;
            bestMatch = key;
          }
        }
      }
      if (bestMatch && highestSimilarity > 0.6) {
        intent = 'general_question';
        answer = CANNED_RESPONSES[bestMatch];
        // Custom logic for payment status only
        if (bestMatch === 'how do i check my payment status' && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0)) {
          const replyBLs = conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs;
          const statusLines = [];
          for (let bl of replyBLs) {
            const status = await getPaymentStatus(bl.trim());
            if (status) {
              statusLines.push(`BL ${bl}: Payment status is '${status}'.`);
            } else {
              statusLines.push(`BL ${bl}: No payment status found.`);
            }
          }
          answer = statusLines.join('\n');
          intent = 'ask_payment_status'; // Override intent if payment status is processed
        }
      } else {
        const aiResponse = await getIntentAndResponse(message, conversationHistory[sender].history, validBLs, invalidBLs);
        intent = aiResponse.intent || 'general_question';
        blNumber = aiResponse.bl_number;
        answer = aiResponse.answer || 'Sorry, an unexpected error occurred.';
      }
    }
  }

  // NEW: Handle specific question types with appropriate responses
  if (isOutOfScope) {
    // Find the most appropriate out-of-scope response
    for (const [key, response] of Object.entries(CANNED_RESPONSES)) {
      if (key.includes('shipment') || key.includes('weather') || key.includes('flight') || key.includes('time')) {
        if (lowerMsg.includes(key.replace(/[^-\w\s]/g, ''))) {
          answer = response;
          break;
        }
      }
    }
    // Default out-of-scope response if no specific match
    if (answer === 'For general enquiries, please provide your BL number or contact support for assistance.') {
      answer = 'We handle CTN processing, not general inquiries. Please contact your shipping carrier for shipment tracking or other logistics services.';
    }
  } else if (isMissingContext) {
    // Check if BL numbers are actually present in the message (might have been missed by pattern)
    const blNumbersInMessage = extractBLNumbers(message);
    if (blNumbersInMessage.length > 0) {
      // BL numbers are present, so this shouldn't be missing context
      // Let it fall through to normal processing
      isMissingContext = false;
      intent = 'general_question'; // Reset to let AI handle it
    } else {
      // Find the most appropriate missing context response
      for (const [key, response] of Object.entries(CANNED_RESPONSES)) {
        if (key.includes('status') || key.includes('invoice') || key.includes('ctn') || key.includes('payment')) {
          if (lowerMsg.includes(key.replace(/[^-\w\s]/g, ''))) {
            answer = response;
            break;
          }
        }
      }
      // Default missing context response if no specific match
      if (answer === 'For general enquiries, please provide your BL number or contact support for assistance.') {
        answer = 'To check the status, please provide your BL number. I can then give you the current status of your CTN processing.';
      }
    }
  } else if (isTechnicalIssue) {
    // Find the most appropriate technical response
    for (const [key, response] of Object.entries(CANNED_RESPONSES)) {
      if (key.includes('website') || key.includes('upload') || key.includes('error') || key.includes('broken')) {
        if (lowerMsg.includes(key.replace(/[^-\w\s]/g, ''))) {
          answer = response;
          break;
        }
      }
    }
    // Default technical response if no specific match
    if (answer === 'For general enquiries, please provide your BL number or contact support for assistance.') {
      answer = 'If you\'re experiencing technical issues, please contact our support team directly. They will help you resolve the problem.';
    }
  } else if (isSecurityQuestion) {
    // Find the most appropriate security response
    for (const [key, response] of Object.entries(CANNED_RESPONSES)) {
      if (key.includes('password') || key.includes('reset') || key.includes('credit card')) {
        if (lowerMsg.includes(key.replace(/[^-\w\s]/g, ''))) {
          answer = response;
          break;
        }
      }
    }
    // Default security response if no specific match
    if (answer === 'For general enquiries, please provide your BL number or contact support for assistance.') {
      answer = 'For security reasons, I cannot provide sensitive account information. Please contact our support team directly.';
    }
  } else if (isMissingContext) {
    // Find the most appropriate missing context response
    for (const [key, response] of Object.entries(CANNED_RESPONSES)) {
      if (key.includes('owe') || key.includes('invoice') || key.includes('ctn') || key.includes('cost') || key.includes('status')) {
        if (lowerMsg.includes(key.replace(/[^-\w\s]/g, ''))) {
          answer = response;
          break;
        }
      }
    }
    // Default missing context response if no specific match
    if (answer === 'For general enquiries, please provide your BL number or contact support for assistance.') {
      answer = 'To help you with your CTN processing, please provide your BL number. I can then give you the specific information you need.';
    }
  }

  // Override intent based on keywords and BL presence, only if explicitly requesting BL data
  if (validBLs.length > 0 || conversationHistory[sender].session.lastValidatedBLs.length > 0) {
    if (/invoice|发票/.test(lowerMsg)) intent = 'request_invoice';
    if (/ctn|container/.test(lowerMsg)) intent = 'ask_ctn_number';
    if (/payment status|check payment/.test(lowerMsg)) intent = 'ask_payment_status';
    // Handle specific pricing questions for specific BLs
    if (/how much|pricing|cost|fee|price/.test(lowerMsg) && validBLs.length > 0) intent = 'ask_pricing';
  } else if (['request_invoice', 'ask_ctn_number', 'ask_payment_status'].includes(intent) && validBLs.length === 0) {
    answer = 'Please provide a BL number to access this information.';
    intent = 'general_question'; // Reset to general to avoid sensitive intent processing
  }
  
  // Additional check: if user mentions a BL number in pricing question, set intent to ask_pricing
  const blNumbersInMessage = extractBLNumbers(message);
  console.log('[DEBUG] BL numbers extracted from message:', blNumbersInMessage);
  if (blNumbersInMessage.length > 0 && /how much|pricing|cost|fee|price/.test(lowerMsg) && !lowerMsg.includes('invoice')) {
    intent = 'ask_pricing';
    console.log('[DEBUG] Set intent to ask_pricing because BL numbers found in message:', blNumbersInMessage);
  }
  
  // Additional check: if user mentions a BL number in status question, set intent to ask_payment_status
  if (blNumbersInMessage.length > 0 && /whats?\s+the\s+status/i.test(lowerMsg)) {
    intent = 'ask_payment_status';
    console.log('[DEBUG] Set intent to ask_payment_status because BL numbers found in status question:', blNumbersInMessage);
  }

  // Custom handling for overpayment and underpayment
  if (/overpaid.*invoice/i.test(lowerMsg)) {
    const replyBLs = validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0 ? 
      (conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs) : [];
    if (replyBLs.length > 0) {
      answer = `For the following BL(s): ${replyBLs.join(', ')}, we will deduct the overpaid amount from your next invoice. Please provide your BL or CTN number if not already included to process this adjustment.`;
    } else {
      answer = `We will deduct the overpaid amount from your next invoice. Please provide your BL or CTN number to process this adjustment.`;
    }
    intent = 'general_question';
  } else if (/underpaid.*invoice/i.test(lowerMsg)) {
    const replyBLs = validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0 ? 
      (conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs) : [];
    if (replyBLs.length > 0) {
      answer = `For the following BL(s): ${replyBLs.join(', ')}, the underpaid difference will be added to your next invoice. Please provide your BL or CTN number if not already included to process this adjustment.`;
    } else {
      answer = `The underpaid difference will be added to your next invoice. Please provide your BL or CTN number to process this adjustment.`;
    }
    intent = 'general_question';
  }

  if (blNumber) validBLs = Array.from(new Set([...validBLs, ...(Array.isArray(blNumber) ? blNumber : [blNumber])]));

  let reply = answer;
  if (invalidBLs.length > 0 && ['request_invoice', 'ask_ctn_number', 'payment_receipt', 'ask_payment_status'].includes(intent)) {
    reply = `Sorry, the BL number(s) ${invalidBLs.join(', ')} could not be found in our system. Please check and try again.`;
  } else if (validBLs.length < blNumbers.length) {
    reply = `Note: The following BL number(s) ${invalidBLs.join(', ')} were not found. Proceeding with valid BL(s): ${validBLs.join(', ')}.`;
  }

  if (paidAmount !== null && validBLs.length > 0) intent = 'payment_receipt';

  // Enforce verification for sensitive intents before proceeding
  // Only allow general pricing questions without verification (no specific BLs mentioned)
  const isGeneralPricingQuestion = intent === 'ask_pricing' && validBLs.length === 0 && blNumbersInMessage.length === 0 && 
    (/how much|pricing|cost|fee|price/.test(lowerMsg));
  
  const needsVerification = ['request_invoice', 'ask_ctn_number', 'ask_payment_status', 'ask_pricing'].includes(intent) && 
    (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0 || blNumbersInMessage.length > 0) &&
    !isGeneralPricingQuestion &&
    !conversationHistory[sender].session.verifiedEmail; // Only need verification if not already verified
  
  console.log('[DEBUG] Verification check - Intent:', intent, 'Valid BLs:', validBLs, 'Pending BLs:', conversationHistory[sender].session.pendingBLs, 'BLs in message:', blNumbersInMessage, 'Is general pricing:', isGeneralPricingQuestion, 'Needs verification:', needsVerification);
  if (needsVerification) {
    // Check if verification has expired
    const verificationAge = Date.now() - (conversationHistory[sender].session.verificationTimestamp || 0);
    const validityPeriod = 7200000; // 2 hours in milliseconds
    if (conversationHistory[sender].session.verifiedEmail && verificationAge > validityPeriod) {
      conversationHistory[sender].session.verifiedEmail = null;
      conversationHistory[sender].session.verificationTimestamp = null;
      reply = 'Your verification has expired. Please provide your registered email to access this information.';
    }
    if (!conversationHistory[sender].session.verifiedEmail) {
      // Use BL numbers from message if no validated BLs available
      const verificationBLs = conversationHistory[sender].session.pendingBLs.length > 0 ? 
        conversationHistory[sender].session.pendingBLs : 
        (validBLs.length > 0 ? validBLs : blNumbersInMessage);
      console.log('[DEBUG] BL numbers for verification:', verificationBLs); // Debug BLs being verified
      if (justProvidedEmail) {
        let allVerified = true;
        for (let bl of verificationBLs) {
          const response = await verifySensitiveAccess({ email: justProvidedEmail, bl_number: bl });
          console.log('[DEBUG] Verification Response for BL', bl, ':', response); // Debug each verification
          if (!response.success) {
            allVerified = false;
            reply = `Cannot access info for BL ${bl}: ${response.message || 'Email verification failed.'}`;
            break;
          }
        }
        if (allVerified) {
          conversationHistory[sender].session.verifiedEmail = justProvidedEmail;
          conversationHistory[sender].session.verificationTimestamp = Date.now(); // Set timestamp on successful verification
          // Always re-process the last sensitive user request if it exists
          if (conversationHistory[sender].session.lastSensitiveRequest) {
            const lastSensitive = conversationHistory[sender].session.lastSensitiveRequest;
            conversationHistory[sender].session.lastSensitiveRequest = null;
            conversationHistory[sender].session.pendingResponse = null;
            // Call chatHandler recursively with the last sensitive message and preserved verification BLs
            return await chatHandler(lastSensitive, sender, { ...context, bl_numbers: verificationBLs, skipBLExtraction: true });
          }
          // Only clear pendingBLs after invoice/CTN/payment response is sent
        }
      } else if (!conversationHistory[sender].session.pendingResponse) {
        reply = 'For security, please provide your registered email to access this information.';
        conversationHistory[sender].session.pendingResponse = reply;
        // Store the sensitive request for later processing after verification
        conversationHistory[sender].session.lastSensitiveRequest = message;
        console.log('[DEBUG] Stored sensitive request for later processing:', message);
        
        // Return early to avoid processing the sensitive request without verification
        if (incomingIsChinese) { 
          reply = await openaiTranslate(reply, 'English', 'Chinese'); 
          if (!/祝商祺|此致敬礼|顺祝商祺|敬请回复/.test(reply)) reply += '\n\n祝商祺！\nIQSTrade客服团队'; 
        }
        
        logMessage('AI_REPLY', { question: message, reply, user: sender, classification: intent, bl_numbers: verificationBLs });
        conversationHistory[sender].history.push({ role: 'assistant', content: reply });
        return reply;
      }
    }
  } else if (conversationHistory[sender].session.pendingResponse && justProvidedEmail) {
    conversationHistory[sender].session.pendingResponse = null;
  }

  // Handle general pricing questions without verification (no specific BLs)
  if (isGeneralPricingQuestion) {
    reply = `Our pricing depends on the number of containers and services required. Please provide your BL number(s) and details for a quote.`;
    
    // Return early to avoid other intent processing
    if (incomingIsChinese) { 
      reply = await openaiTranslate(reply, 'English', 'Chinese'); 
      if (!/祝商祺|此致敬礼|顺祝商祺|敬请回复/.test(reply)) reply += '\n\n祝商祺！\nIQSTrade客服团队'; 
    }
    
    logMessage('AI_REPLY', { question: message, reply, user: sender, classification: 'ask_pricing', bl_numbers: [] });
    conversationHistory[sender].history.push({ role: 'assistant', content: reply });
    return reply;
  }

  // Always return both invoice and CTN if both are requested and user is verified, regardless of intent
  const wantsInvoice = /invoice|发票/.test(lowerMsg);
  const wantsCTN = /ctn|container/.test(lowerMsg);
  if ((wantsInvoice && wantsCTN) && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0) && conversationHistory[sender].session.verifiedEmail) {
    let replyBLs = conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs;
    // Filter out any BLs that contain a comma or whitespace (combined BLs)
    replyBLs = replyBLs.filter(bl => typeof bl === 'string' && !bl.includes(',') && !/\s/.test(bl));
    
    // Check if there are invalid BLs that should be reported
    const allBLsInMessage = extractBLNumbers(message);
    const invalidBLsInMessage = allBLsInMessage.filter(bl => !validBLs.includes(bl));
    
    const replyLines = [];
    
    // Add error message for invalid BLs if any
    if (invalidBLsInMessage.length > 0) {
      replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
    }
    
    for (let bl of replyBLs) {
      // Invoice
      const result = await getInvoiceLink(bl.trim());
      if (result.length > 0 && result[0].invoice_filename) {
        replyLines.push(`For BL ${bl}: Here's your invoice: ${result[0].invoice_filename}`);
      } else {
        replyLines.push(`For BL ${bl}: Invoice not yet issued. Please contact support.`);
      }
      // CTN
      const ctn = await getUniqueNumber(bl.trim());
      if (ctn) {
        replyLines.push(`For BL ${bl}: CTN number is ${ctn}.`);
      } else {
        replyLines.push(`For BL ${bl}: No CTN number found.`);
      }
    }
    reply = replyLines.join('\n');
    conversationHistory[sender].session.pendingBLs = [];
    // Return early so that intent-based blocks below do not override this reply
    logMessage('AI_REPLY', { question: message, reply, user: sender, classification: 'invoice_and_ctn', bl_numbers: replyBLs });
    conversationHistory[sender].history.push({ role: 'assistant', content: reply });
    return reply;
  } else if (intent === 'request_invoice' && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0) && conversationHistory[sender].session.verifiedEmail) {
    // Use all valid BLs from the message, not just pendingBLs
    const allBLsInMessage = extractBLNumbers(message);
    const validBLsInMessage = allBLsInMessage.filter(bl => validBLs.includes(bl));
    const invalidBLsInMessage = allBLsInMessage.filter(bl => !validBLs.includes(bl));
    
    const replyBLs = validBLsInMessage.length > 0 ? validBLsInMessage : 
                    (conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs);
    
    console.log('[DEBUG] BLs used for invoice response:', replyBLs); // Debug BLs for response
    
    const replyLines = [];
    
    // Add error message for invalid BLs if any
    if (invalidBLsInMessage.length > 0) {
      replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
    }
    
    // Process valid BLs
    for (let bl of replyBLs) {
      const result = await getInvoiceLink(bl.trim());
      console.log('[DEBUG] getInvoiceLink DB rows for', bl, ':', result); // Debug DB query
      replyLines.push(result.length > 0 && result[0].invoice_filename
        ? `For BL ${bl}: Here's your invoice: ${result[0].invoice_filename}`
        : `For BL ${bl}: Invoice not yet issued. Please contact support.`);
    }
    reply = replyLines.join('\n');
    conversationHistory[sender].session.pendingBLs = []; // Clear after response
  } else if (intent === 'ask_ctn_number' && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0) && conversationHistory[sender].session.verifiedEmail) {
    // Use all valid BLs from the message, not just pendingBLs
    const allBLsInMessage = extractBLNumbers(message);
    const validBLsInMessage = allBLsInMessage.filter(bl => validBLs.includes(bl));
    const invalidBLsInMessage = allBLsInMessage.filter(bl => !validBLs.includes(bl));
    
    const replyBLs = validBLsInMessage.length > 0 ? validBLsInMessage : 
                    (conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs);
    
    console.log('[DEBUG] BLs used for CTN response:', replyBLs); // Debug BLs for response
    
    const replyLines = [];
    
    // Add error message for invalid BLs if any
    if (invalidBLsInMessage.length > 0) {
      replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
    }
    
    // Process valid BLs with contextual responses
    for (let bl of replyBLs) {
      const ctn = await getUniqueNumber(bl.trim());
      const paymentStatus = await getPaymentStatus(bl.trim());
      
      // Check if this is a "ready" question and provide contextual response
      if (lowerMsg.includes('ready') && paymentStatus === 'Awaiting Bank In') {
        replyLines.push(`For BL ${bl}: The CTN is still processing since the payment status is 'Awaiting Bank In'. Once payment is confirmed, the CTN will be issued.`);
      } else if (ctn) {
        replyLines.push(`For BL ${bl}: CTN number is ${ctn}.`);
      } else {
        replyLines.push(`For BL ${bl}: No CTN number found.`);
      }
    }
    reply = replyLines.join('\n');
    conversationHistory[sender].session.pendingBLs = []; // Clear after response
  } else if (intent === 'ask_payment_status' && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0) && conversationHistory[sender].session.verifiedEmail) {
    // Use all valid BLs from the message, not just pendingBLs
    const allBLsInMessage = extractBLNumbers(message);
    const validBLsInMessage = allBLsInMessage.filter(bl => validBLs.includes(bl));
    const invalidBLsInMessage = allBLsInMessage.filter(bl => !validBLs.includes(bl));
    
    const replyBLs = validBLsInMessage.length > 0 ? validBLsInMessage : 
                    (conversationHistory[sender].session.pendingBLs.length > 0 ? conversationHistory[sender].session.pendingBLs : validBLs);
    
    console.log('[DEBUG] BLs used for payment status response:', replyBLs); // Debug BLs for response
    
    const replyLines = [];
    
    // Add error message for invalid BLs if any
    if (invalidBLsInMessage.length > 0) {
      replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
    }
    
    // Process valid BLs
    for (let bl of replyBLs) {
      const status = await getPaymentStatus(bl.trim());
      replyLines.push(status ? `For BL ${bl}: Payment status is '${status}'.` : `For BL ${bl}: No payment status found.`);
    }
    reply = replyLines.join('\n');
    conversationHistory[sender].session.pendingBLs = []; // Clear after response
  } else if (intent === 'payment_receipt' && validBLs.length > 0 && paidAmount !== null) {
    // Check if there are invalid BLs that should be reported
    const allBLsInMessage = extractBLNumbers(message);
    const invalidBLsInMessage = allBLsInMessage.filter(bl => !validBLs.includes(bl));
    console.log('[DEBUG] Payment receipt processing - all BLs in message:', allBLsInMessage, 'invalid BLs:', invalidBLsInMessage);
    
    // Ensure validBLs contains only individual BL numbers, not concatenated ones
    const cleanValidBLs = validBLs.filter(bl => typeof bl === 'string' && !bl.includes(',') && !bl.includes(' '));
    console.log('[DEBUG] Cleaned valid BLs for payment processing:', cleanValidBLs);
    
    let invoiceSum = 0, invoiceDetails = [];
    console.log('[DEBUG] Getting invoice info for BLs:', cleanValidBLs);
    const invoiceInfos = await getInvoiceInfo(cleanValidBLs);
    console.log('[DEBUG] Invoice info returned:', invoiceInfos);
    
    // Process payments and build invoice details
    let validPayments = [];
    
    for (let bl of cleanValidBLs) {
      const info = invoiceInfos.find(row => row.bl_number === bl);
      if (info) {
        validPayments.push({ bl, info });
        console.log('[DEBUG] Processing BL:', bl);
        console.log('[DEBUG] Found info for BL', bl, ':', info);
        if (info && (info.ctn_fee !== undefined || info.service_fee !== undefined)) {
          const ctnFee = Number(info.ctn_fee) || 0, serviceFee = Number(info.service_fee) || 0;
          const balanceApplied = Number(info.balance_applied) || 0;
          const amount = (ctnFee + serviceFee) - balanceApplied;
          invoiceSum += amount;
          invoiceDetails.push(`BL ${bl}: $${amount} (CTN Fee: $${ctnFee}, Service Fee: $${serviceFee}${balanceApplied > 0 ? `, Balance Applied: -$${balanceApplied}` : ''})`);
        } else {
          invoiceDetails.push(`BL ${bl}: No fee data found in DB.`);
        }
      }
    }
    const diff = paidAmount - invoiceSum;
    
    let replyLines = [];
    
    // Add error message for invalid BLs if any
    if (invalidBLsInMessage.length > 0) {
      replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
    }
    
    if (invoiceSum > 0) {
      if (Math.abs(diff) < 0.01 || diff > 0) {
        // Check for duplicates BEFORE processing payments
        let duplicatePayments = [];
        let validPaymentsToProcess = [];
        
        console.log(`[PAYMENT DEBUG] Starting duplicate check for ${validPayments.length} payments`);
        
        for (let { bl, info } of validPayments) {
          console.log(`[DUPLICATE CHECK] Checking for duplicate payment - BL: ${bl}, ID: ${info.id}`);
          console.log(`[DUPLICATE CHECK] BL info:`, JSON.stringify(info, null, 2));
          
          const isDuplicate = await checkPaymentProcessed(info.id, 'whatsapp');
          console.log(`[DUPLICATE CHECK] Duplicate check result for BL ${bl} (ID: ${info.id}): ${isDuplicate}`);
          
          if (isDuplicate) {
            duplicatePayments.push(bl);
            console.log(`[DUPLICATE CHECK] ✅ Duplicate payment detected for BL ${bl} (ID: ${info.id})`);
          } else {
            validPaymentsToProcess.push({ bl, info });
            console.log(`[DUPLICATE CHECK] ✅ Valid payment for BL ${bl} (ID: ${info.id})`);
          }
        }
        
        console.log(`[PAYMENT DEBUG] Duplicate check complete. Duplicates: ${duplicatePayments.length}, Valid: ${validPaymentsToProcess.length}`);
        
        // Handle duplicate payments first
        if (duplicatePayments.length > 0) {
          let duplicateMessage = `⚠️ Duplicate Payment Alert: We detected duplicate payment attempts for BL(s): ${duplicatePayments.join(', ')}. These payments have already been processed. No action needed.`;
          replyLines.push(duplicateMessage);
          
          // Send duplicate payment notifications for each duplicate
          for (let bl of duplicatePayments) {
            try {
              const blInfo = validPayments.find(p => p.bl === bl);
              if (blInfo) {
                // Send duplicate payment notifications
                await sendDuplicatePaymentNotifications(
                  blInfo.info.customer_email,
                  blInfo.info.customer_username,
                  bl,
                  'whatsapp',
                  await getOriginalPaymentDate(blInfo.info.id, 'whatsapp')
                );
                console.log(`[DUPLICATE CHECK] Duplicate payment notifications sent for BL ${bl} (ID: ${blInfo.info.id})`);
              }
            } catch (error) {
              console.error(`[ERROR] Failed to send duplicate payment notifications for BL ${bl}:`, error);
            }
          }
        }
        
        // Process only non-duplicate payments
        if (validPaymentsToProcess.length > 0) {
          let paymentMessage = `We received your payment of $${paidAmount}, which matches the total invoice amount for BL(s):\n${invoiceDetails.join('\n')}`;
          if (diff > 0) paymentMessage += `\nYou have overpaid by $${diff.toFixed(2)}. Please contact support for a refund or to allocate the excess.`;
          paymentMessage += '\nA receipt will be generated and sent to you shortly.';
          replyLines.push(paymentMessage);
          
          // Process payments and mark as processed
          for (let { bl, info } of validPaymentsToProcess) {
            try {
              console.log(`[PAYMENT PROCESSING] 🔄 Starting processing for BL ${bl} (ID: ${info.id}) for customer: ${info.customer_username}`);
              
              // Mark payment as processed FIRST
              console.log(`[PAYMENT PROCESSING] 📝 Marking payment as processed for BL ${bl} (ID: ${info.id})`);
              await markPaymentProcessed(info.id, 'whatsapp', 'whatsapp_chat');
              console.log(`[PAYMENT PROCESSING] ✅ Payment marked as processed for BL ${bl} (ID: ${info.id})`);
              
              // Process balance if customer username exists
              if (info.customer_username) {
                const ctnFee = Number(info.ctn_fee) || 0;
                const serviceFee = Number(info.service_fee) || 0;
                const balanceApplied = Number(info.balance_applied) || 0;
                const invoiceAmount = (ctnFee + serviceFee) - balanceApplied;
                
                console.log(`[PAYMENT PROCESSING] 💰 Processing balance for ${info.customer_username}: invoice=${invoiceAmount}`);
                
                // Process the invoice payment (customer pays the exact invoice amount)
                const balanceAdjustment = await processPaymentBalance(
                  info.customer_username,
                  invoiceAmount, // Customer pays exactly what they owe
                  invoiceAmount, // Invoice amount
                  info.id,
                  'whatsapp',
                  'whatsapp_chat'
                );
                
                console.log(`[PAYMENT PROCESSING] ✅ Balance adjustment completed for ${info.customer_username}: ${balanceAdjustment}`);
              } else {
                console.log(`[PAYMENT PROCESSING] ⚠️ No customer_username found for BL ${bl}, skipping balance processing`);
              }
              
              console.log(`[PAYMENT PROCESSING] ✅ Completed processing for BL ${bl} (ID: ${info.id})`);
            } catch (error) {
              console.error(`[ERROR] Failed to process payment for BL ${bl}:`, error);
            }
          }
          
          // Handle overpayment after all BLs are processed
          if (diff > 0) {
            console.log(`[PAYMENT PROCESSING] 🌍 Processing overpayment of ${diff} for all customers`);
            console.log(`[PAYMENT PROCESSING] 📊 Payment details: paidAmount=${paidAmount}, invoiceSum=${invoiceSum}, diff=${diff}`);
            
            // Get unique customers from the processed BLs
            const uniqueCustomers = [...new Set(validPaymentsToProcess.map(p => p.info.customer_username).filter(Boolean))];
            console.log(`[PAYMENT PROCESSING] 👥 Unique customers found: ${uniqueCustomers.join(', ')}`);
            
            if (uniqueCustomers.length > 0) {
              // Split overpayment equally among customers
              const overpaymentPerCustomer = diff / uniqueCustomers.length;
              console.log(`[PAYMENT PROCESSING] 💰 Overpayment per customer: ${overpaymentPerCustomer} (total: ${diff}, customers: ${uniqueCustomers.length})`);
              
              for (const customerUsername of uniqueCustomers) {
                console.log(`[PAYMENT PROCESSING] 💰 Adding overpayment credit of ${overpaymentPerCustomer} for ${customerUsername}`);
                
                // Get the first BL info for this customer to use as reference
                const firstBLForCustomer = validPaymentsToProcess.find(p => p.info.customer_username === customerUsername);
                
                const overpaymentResult = await processPaymentBalance(
                  customerUsername,
                  overpaymentPerCustomer,
                  0, // No invoice amount for overpayment
                  firstBLForCustomer.info.id,
                  'whatsapp',
                  'whatsapp_chat'
                );
                
                console.log(`[PAYMENT PROCESSING] ✅ Overpayment credit result for ${customerUsername}: ${overpaymentResult}`);
                
                // Add a separate transaction record specifically for overpayment
                try {
                  await pool.query(
                    `INSERT INTO customer_balance_transactions 
                     (username, transaction_type, amount, reference_type, reference_id, payment_source, description, created_by)
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
                    [
                      customerUsername,
                      'credit',
                      overpaymentPerCustomer,
                      'bill_of_lading',
                      firstBLForCustomer.info.id,
                      'whatsapp',
                      `Overpayment credit: Paid $${paidAmount}, Invoice $${invoiceSum}`,
                      'whatsapp_chat'
                    ]
                  );
                  console.log(`[PAYMENT PROCESSING] 📝 Overpayment transaction recorded for ${customerUsername}: $${overpaymentPerCustomer}`);
                } catch (error) {
                  console.error(`[ERROR] Failed to record overpayment transaction for ${customerUsername}:`, error);
                }
              }
            } else {
              console.log(`[PAYMENT PROCESSING] ⚠️ No customers found for overpayment processing`);
            }
          } else {
            console.log(`[PAYMENT PROCESSING] ℹ️ No overpayment to process (diff: ${diff})`);
          }
          
          try {
            const validBLNumbers = validPaymentsToProcess.map(p => p.bl);
            const pdfPath = await generateReceiptPDF({ blNumbers: validBLNumbers, paidAmount, invoiceDetails, customerName: '' });
            const receiptUrl = await uploadReceiptToCloudinary(pdfPath);
            await updateBLStatusAndReceipt(validBLNumbers, receiptUrl);
            fs.unlink(pdfPath, () => {});
          } catch (e) { console.error('[ERROR] Receipt generation failed:', e); }
        }
      } else if (diff < 0) {
        replyLines.push(`We received your payment of $${paidAmount}, but the total invoice amount for BL(s) is $${invoiceSum}.\n${invoiceDetails.join('\n')}\nYou have underpaid by $${Math.abs(diff).toFixed(2)}. Please pay the remaining amount.`);
      }
    } else {
      replyLines.push(`We detected a payment of $${paidAmount} for BL number(s): ${validPayments.map(p => p.bl).join(', ')}. If you need a receipt, let us know.`);
    }
    
    reply = replyLines.join('\n\n');
  } else if (intent === 'ask_payment_methods') reply = `We accept the following payment methods:\n• Bank Transfer\n• Allinpay\n• Stripe`;
  else if (intent === 'ask_pricing' && (validBLs.length > 0 || conversationHistory[sender].session.pendingBLs.length > 0) && conversationHistory[sender].session.verifiedEmail) {
    // Check if BL numbers are provided in the message
    const blNumbersInMessage = extractBLNumbers(message);
    
    if (blNumbersInMessage.length > 0) {
      // BL numbers provided - fetch specific pricing from database
      try {
        const invoiceInfo = await getInvoiceInfo(blNumbersInMessage);
        
        // Check if there are invalid BLs that should be reported
        const invalidBLsInMessage = blNumbersInMessage.filter(bl => !validBLs.includes(bl));
        
        if (invoiceInfo.length > 0) {
          let pricingDetails = [];
          let totalCTNFee = 0;
          let totalServiceFee = 0;
          
          for (const info of invoiceInfo) {
            const ctnFee = Number(info.ctn_fee) || 0;
            const serviceFee = Number(info.service_fee) || 0;
            const balanceApplied = Number(info.balance_applied) || 0;
            totalCTNFee += ctnFee;
            totalServiceFee += serviceFee;
            
            const adjustedTotal = (ctnFee + serviceFee) - balanceApplied;
            pricingDetails.push(`BL ${info.bl_number}: CTN Fee $${ctnFee}, Service Fee $${serviceFee}${balanceApplied > 0 ? `, Balance Applied -$${balanceApplied}` : ''}, Total $${adjustedTotal}`);
          }
          
          const totalFee = (totalCTNFee + totalServiceFee) - (invoiceInfo.reduce((sum, info) => sum + (Number(info.balance_applied) || 0), 0));
          
          let replyLines = [];
          
          // Add error message for invalid BLs if any
          if (invalidBLsInMessage.length > 0) {
            replyLines.push(`Sorry, the BL number(s) ${invalidBLsInMessage.join(', ')} could not be found in our system. Please check and try again.`);
          }
          
          if (invoiceInfo.length === 1) {
            const balanceApplied = Number(invoiceInfo[0].balance_applied) || 0;
            const ctnFee = Number(invoiceInfo[0].ctn_fee) || 0;
            const serviceFee = Number(invoiceInfo[0].service_fee) || 0;
            replyLines.push(`For BL ${invoiceInfo[0].bl_number}:\n• CTN Fee: $${ctnFee}\n• Service Fee: $${serviceFee}${balanceApplied > 0 ? `\n• Balance Applied: -$${balanceApplied}` : ''}\n• Total: $${totalFee}`);
          } else {
            const totalBalanceApplied = invoiceInfo.reduce((sum, info) => sum + (Number(info.balance_applied) || 0), 0);
            replyLines.push(`Pricing for your BL numbers:\n${pricingDetails.join('\n')}\n• Total CTN Fee: $${totalCTNFee}\n• Total Service Fee: $${totalServiceFee}${totalBalanceApplied > 0 ? `\n• Total Balance Applied: -$${totalBalanceApplied}` : ''}\n• Grand Total: $${totalFee}`);
          }
          
          reply = replyLines.join('\n\n');
        } else {
          reply = `I couldn't find pricing information for the BL number(s) you provided. Please check the BL number(s) and try again.`;
        }
      } catch (error) {
        console.error('Error fetching pricing from database:', error);
        reply = `Our pricing depends on the number of containers and services required. Please provide your BL number(s) and details for a quote.`;
      }
    } else {
      // No BL numbers provided - use generic pricing message
      reply = `Our pricing depends on the number of containers and services required. Please provide your BL number(s) and details for a quote.`;
    }
  } else if (intent === 'ask_pricing') {
    // General pricing question without BL numbers - no verification required
    reply = `Our pricing depends on the number of containers and services required. Please provide your BL number(s) and details for a quote.`;
  }

  if (incomingIsChinese) { reply = await openaiTranslate(reply, 'English', 'Chinese'); if (!/祝商祺|此致敬礼|顺祝商祺|敬请回复/.test(reply)) reply += '\n\n祝商祺！\nIQSTrade客服团队'; }

  logMessage('AI_REPLY', { question: message, reply, user: sender, classification: intent || 'general', bl_numbers: validBLs });
  conversationHistory[sender].history.push({ role: 'assistant', content: reply });
  return reply;
}

function calculateSimilarity(str1, str2) {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;
  const similarities = [];
  for (let i = 0; i <= longer.length - shorter.length; i++) {
    let matches = 0;
    for (let j = 0; j < shorter.length; j++) {
      if (longer[i + j] === shorter[j]) matches++;
    }
    similarities.push(matches / shorter.length);
  }
  return similarities.length > 0 ? Math.max(...similarities) : 0;
}

module.exports = chatHandler;


