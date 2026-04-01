const { handleWhatsAppMessage, handleWelcomeMessage } = require('./whatsappEscalation');

// Conversation history tracking for escalation (separate from main logic)
const conversationHistory = new Map();

function addToConversationHistory(sender, message, fromCustomer = true) {
  if (!conversationHistory.has(sender)) {
    conversationHistory.set(sender, []);
  }
  
  const history = conversationHistory.get(sender);
  history.push({
    content: message,
    fromCustomer: fromCustomer,
    timestamp: new Date().toISOString()
  });
  
  // Keep only last 10 messages
  if (history.length > 10) {
    history.shift();
  }
  
  conversationHistory.set(sender, history);
}

function getConversationHistory(sender) {
  return conversationHistory.get(sender) || [];
}

/**
 * Wrapper function that checks for escalation before calling the original chatHandler
 * This preserves all existing logic while adding escalation capability
 */
async function escalationWrapper(originalChatHandler, message, sender, context = {}, whatsappClient = null) {
  try {
    // Add customer message to conversation history
    addToConversationHistory(sender, message, true);
    
    // Check for escalation first
    const customerData = {
      name: 'Unknown Customer', // You can enhance this with actual customer data
      phone: sender,
      email: 'No email provided'
    };
    
    const conversationHistory = getConversationHistory(sender);
    
    // Check for escalation first
    const escalationResult = await handleWhatsAppMessage(message, customerData, conversationHistory, whatsappClient);
    
    if (escalationResult.escalation_requested) {
      // Send escalation response
      const reply = escalationResult.response;
      console.log('🚨 Escalation triggered by', sender);
      
      // Add bot response to conversation history
      addToConversationHistory(sender, reply, false);
      
      return reply;
    }
    
    // Check for welcome message if not escalation
    const welcomeResult = await handleWelcomeMessage(message, customerData, conversationHistory, whatsappClient);
    
    if (welcomeResult.welcome_sent) {
      // Send welcome response
      const reply = welcomeResult.response;
      console.log('👋 Welcome message sent to', sender);
      
      // Add bot response to conversation history
      addToConversationHistory(sender, reply, false);
      
      return reply;
    }
    
    // Continue with normal bot processing using original logic
    const reply = await originalChatHandler(message, sender, context);
    
    // Add bot response to conversation history
    if (reply) {
      addToConversationHistory(sender, reply, false);
    }
    
    return reply;
    
  } catch (error) {
    console.error('Error in escalation wrapper:', error);
    // Fallback to original handler if escalation fails
    return await originalChatHandler(message, sender, context);
  }
}

module.exports = {
  escalationWrapper,
  addToConversationHistory,
  getConversationHistory
}; 