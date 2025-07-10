import React from 'react';
import { Typography, Box, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function FAQ({ t = x => x }) {
  const faqs = [
    {
      question: t('faqQ1'),
      answer: t('faqA1')
    },
    {
      question: t('faqQ2'),
      answer: t('faqA2')
    },
    {
      question: t('faqQ3'),
      answer: t('faqA3')
    },
    {
      question: t('faqQ4'),
      answer: t('faqA4')
    },
    {
      question: t('faqQ5'),
      answer: t('faqA5')
    },
    {
      question: t('faqQ6'),
      answer: t('faqA6')
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