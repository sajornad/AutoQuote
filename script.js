function getConfig() {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(xhr.statusText);
          }
        }
      };
      xhr.open('GET', 'config.json', true);
      xhr.send();
    });
  }

function formatDateForFileName(date) {
    return date.replace(/\//g, '_');
  }
  
  function generateQRCode(url) {
    const qrCodeContainer = document.createElement('div');
    new QRCode(qrCodeContainer, url);
  
    return qrCodeContainer;
  }

  function qrCodeToDataURL(qrCodeElement) {
    const canvas = qrCodeElement.querySelector('canvas');
    return canvas.toDataURL('image/png');
  }
  

    function formatPrice(price) {
    const formattedPrice = parseFloat(price).toFixed(2).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return formattedPrice;
  }
  

function getBase64Image(url, callback) {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = function () {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.height = img.height;
      canvas.width = img.width;
      ctx.drawImage(img, 0, 0);
      const dataURL = canvas.toDataURL('image/png');
      callback(dataURL);
    };
    img.src = url;
  }
  
  function createNewItem() {
    const itemContainer = document.createElement('div');
    itemContainer.className = 'item';
  
    const itemCount = document.querySelectorAll('.item').length + 1;
  
    const itemLabel = document.createElement('label');
    itemLabel.htmlFor = `item-${itemCount}`;
    itemLabel.textContent = 'Item:';
    itemContainer.appendChild(itemLabel);
  
    const itemInput = document.createElement('input');
    itemInput.type = 'text';
    itemInput.id = `item-${itemCount}`;
    itemInput.name = `item-${itemCount}`;
    itemInput.required = true;
    itemContainer.appendChild(itemInput);
  
    itemContainer.appendChild(document.createElement('br'));
  
    const priceLabel = document.createElement('label');
    priceLabel.htmlFor = `price-${itemCount}`;
    priceLabel.textContent = 'Price:';
    itemContainer.appendChild(priceLabel);
  
    const priceInput = document.createElement('input');
    priceInput.type = 'number';
    priceInput.id = `price-${itemCount}`;
    priceInput.name = `price-${itemCount}`;
    priceInput.required = true;
    itemContainer.appendChild(priceInput);
  
    itemContainer.appendChild(document.createElement('br'));
  
    return itemContainer;
  }

  
  function readLogoFile(file, callback) {
    const reader = new FileReader();
    reader.onload = function (event) {
      callback(event.target.result);
    };
    reader.readAsDataURL(file);
  }
  
  document.getElementById('add-item').addEventListener('click', () => {
    const newItem = createNewItem();
    document.getElementById('items-container').appendChild(newItem);
  });

  
  
  document.getElementById('quote-form').addEventListener('submit', async (event) => {
    event.preventDefault();

    // Get the configuration from the config.json file
    const config = await getConfig();

  
    const clientName = document.getElementById('client-name').value;
    const date = document.getElementById('date').value;
    const conditions = document.getElementById('conditions').value;
  
    const logoInput = document.getElementById('logo');
    const logoFile = logoInput.files[0];
  
    
    // Use a default logo URL if no logo is uploaded
    // Replace the defaultLogoUrl and baseURL variables with values from the configuration
    const defaultLogoUrl = config.defaultLogoUrl;
    const baseURL = config.HOST;
  
    function generatePDF(logoDataURL) {
      const doc = new jsPDF();
  
      doc.addImage(logoDataURL, 'PNG', 10, 10, 50, 25);
      doc.setFontSize(18);
      doc.text(`Quote for ${clientName}`, 70, 20);
  
      doc.setFontSize(14);
      doc.text(`Date: ${date}`, 10, 50);
  
      const items = document.querySelectorAll('.item');
      let yOffset = 60;
      items.forEach((item, index) => {
        const itemName = item.querySelector('input[type="text"]').value;
        const itemPrice = item.querySelector('input[type="number"]').value;
  
        doc.text(`Item ${index + 1}: ${itemName}`, 10, yOffset);
        yOffset += 10;
        doc.text(`Price ${index + 1}: $${formatPrice(itemPrice)}`, 10, yOffset);
        yOffset += 10;
      });

  
      doc.text('Conditions of Payment:', 10, yOffset);
      yOffset += 10;
      doc.setFontSize(12);
      doc.text(doc.splitTextToSize(conditions, 180), 10, yOffset);
  
      const formattedDate = formatDateForFileName(date);
      
      // Generate the QR code (replace the baseURL with your server's URL)
      const baseURL = 'https://360.3govideo.com/fast-quote'; // Replace with your server's URL
      const pdfFileName = config.fileNameTemplate
                        .replace('{clientName}', clientName)
                        .replace('{date}', formattedDate);

      const pdfURL = `${baseURL}/${pdfFileName}`;
      
      // Display the QR code on the page
      //const qrCode = generateQRCode(pdfURL);
      //document.body.appendChild(qrCode);

    // Create the QR code element
    const qrCodeElement = generateQRCode(pdfURL);

    // Convert the QR code to a data URL and add it to the PDF
    const qrCodeDataURL = qrCodeToDataURL(qrCodeElement);
    doc.addImage(qrCodeDataURL, 'PNG', 150, 10, 50, 50);

    // Save the updated PDF with the QR code
    doc.save(pdfFileName);




    }
  
    if (logoFile) {
      readLogoFile(logoFile, (logoDataURL) => {
        generatePDF(logoDataURL);
      });
    } else {
      getBase64Image(defaultLogoUrl, (defaultLogoDataURL) => {
        generatePDF(defaultLogoDataURL);
      });
    }
  });
  