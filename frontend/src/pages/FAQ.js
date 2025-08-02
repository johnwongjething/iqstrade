import React from 'react';
import { Typography, Box, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function FAQ({ t = x => x }) {
  const faqs = [
    {
      question: "How long does it take to process a CTN?",
      answer: "The processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. The exact time can vary depending on the payment method used."
    },
    {
      question: "What payment methods do you accept?",
      answer: "We accept the following payment methods: Bank Transfer, Allinpay, and Stripe. Please choose the one that is most convenient for you. Instructions are provided when you generate a payment link."
    },
    {
      question: "How much do you charge for CTN and service fees?",
      answer: "Our current fee structure is as follows: CTN Fee: $100 per container, Service Fee: $100 per container. This amounts to a total of $200 per container. Please note that this pricing is for Bill of Lading (ocean freight) and may differ for Air Waybills."
    },
    {
      question: "How do I get a copy of my invoice?",
      answer: "You can request a copy of your invoice by replying to your confirmation email or by logging into your account on our portal. If you need assistance, please provide your B/L or CTN number."
    },
    {
      question: "How do I track the status of my CTN?",
      answer: "To check the status of your Cargo Tracking Note (CTN), please provide your B/L or CTN number. We will update you as soon as possible."
    },
    {
      question: "What documents do I need to provide for CTN processing?",
      answer: "For CTN processing, please provide the following documents: Bill of Lading (B/L), Commercial Invoice, Packing List, and any other relevant shipping documents. If you have already submitted these, no further action is needed."
    },
    {
      question: "How do I upload my bank transfer receipt?",
      answer: "You can upload your bank transfer receipt by replying to your confirmation email with the receipt attached. Our team will process your payment as soon as it is received."
    },
    {
      question: "Can I get a refund or cancel my CTN?",
      answer: "Refunds or cancellations are handled on a case-by-case basis. Please provide your B/L or CTN number and the reason for your request, and our team will review your case."
    },
    {
      question: "What is the difference between CTN and B/L?",
      answer: "A Bill of Lading (B/L) is a shipping document issued by the carrier, while a Cargo Tracking Note (CTN) is a regulatory document required by certain countries for cargo tracking and compliance. Both are important for your shipment."
    },
    {
      question: "What are your business hours?",
      answer: "Our business hours are Monday to Friday, 9:00 AM to 6:00 PM (local time). We aim to respond to all enquiries within one business day."
    },
    {
      question: "How do I contact support?",
      answer: "You can contact our support team by replying to your confirmation email or calling our hotline at [your phone number]. We are here to help!"
    },
    {
      question: "Can I pay in a different currency?",
      answer: "Currently, we accept payments in USD. If you wish to pay in another currency, please contact us in advance to discuss available options."
    },
    {
      question: "How do I update my company/contact information?",
      answer: "To update your company or contact information, please reply to your confirmation email with the new details, or update your profile in our online portal."
    }
  ];
  return (
    <Box
      sx={{
        backgroundImage: 'url(/assets/faq.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        minHeight: '100vh',
        py: 8,
      }}
    >
      <Box maxWidth="md" sx={{ mx: 'auto', background: 'rgba(255,255,255,0.95)', borderRadius: 2, py: 4, px: 4, mt: 6 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          {t('faqHeader')}
        </Typography>
        {faqs.map((faq, idx) => (
          <Accordion key={idx} sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">{faq.question}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography>{faq.answer}</Typography>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </Box>
  );
}

export default FAQ;