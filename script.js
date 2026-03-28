document.addEventListener('DOMContentLoaded', () => {
    const aiForm = document.getElementById('ai-form');
    const inputView = document.getElementById('input-view');
    const loadingView = document.getElementById('loading-view');
    const resultView = document.getElementById('result-view');
    const btnRecreate = document.getElementById('btn-recreate');
    const resProject = document.getElementById('res-project');

    const steps = [
        document.getElementById('step-0'),
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4'),
        document.getElementById('step-5'),
        document.getElementById('step-6'),
        document.getElementById('step-7')
    ];

    aiForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get Input
        const projectName = document.getElementById('projectName').value;
        const locationName = document.getElementById('location').value;
        const propertyType = document.getElementById('propertyType').options[document.getElementById('propertyType').selectedIndex].text;
        const objective = document.getElementById('objective').value;

        resProject.textContent = `${projectName.toUpperCase()} (${propertyType.toUpperCase()})`;

        // Trigger loading screen
        inputView.classList.add('hidden');
        loadingView.classList.remove('hidden');

        // Reset steps
        steps.forEach(step => {
            step.className = 'pending';
            step.querySelector('.status-badge').textContent = 'Đợi';
        });

        // 1. Dựng hàm chạy giả lập Animation UI (8 bước nhỏ tương ứng 8 giây)
        let isBackendDone = false;
        let finalData = null;

        function animateSteps(stepIndex) {
            if (stepIndex >= steps.length) return;
            const stepEl = steps[stepIndex];
            stepEl.className = 'processing';
            stepEl.querySelector('.status-badge').textContent = 'Đang Quét...';

            setTimeout(() => {
                stepEl.className = 'done';
                stepEl.querySelector('.status-badge').textContent = 'Hoàn Tất ✅';
                
                // Nếu backend trả về rồi (hơn 8 giây), chạy nhanh các bước còn lại và hiện kết quả
                if (isBackendDone && stepIndex === steps.length - 1) {
                    showResults(finalData);
                } else if(stepIndex < steps.length - 1) {
                    animateSteps(stepIndex + 1);
                }
            }, 1000); // 1 giây 1 bước (Mô phỏng UI)
        }

        // Bắt đầu chạy Animation
        animateSteps(0);

        // 2. Fetch DATA THẬT TỪ BACKEND
        try {
            const resp = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ projectName, locationName, propertyType, objective })
            });
            finalData = await resp.json();
            isBackendDone = true;
            
            // Check logic API ngầm
            if (finalData.status === "error") {
                alert(`HỆ THỐNG DỪNG LẠI: ${finalData.message}`);
                // Phá huỷ animation và hiển thị lại hộp nhập để User không bị treo
                resultView.classList.add('hidden');
                loadingView.classList.add('hidden');
                inputView.classList.remove('hidden');
                return;
            }

            // Nếu animation đã chạy xong toàn bộ các bước mà backend giờ mới trả về, thì show kết quả ngay!
            const lastStep = steps[steps.length - 1];
            if (lastStep.classList.contains('done')) {
                showResults(finalData);
            }
        } catch(err) {
            alert('Lỗi kết nối Backend AI!');
            console.error(err);
        }
    });

    function downloadString(filename, text) {
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }

    function showResults(data) {
        if (!data) return;
        // Inject data into DOM
        document.querySelector('.score-badge span').textContent = data.score;
        document.querySelector('.stat-grid .stat:nth-child(1) .value').innerHTML = `${data.financials.yield}<span class="unit">%</span>`;
        document.querySelector('.stat-grid .stat:nth-child(2) .value').innerHTML = `${data.financials.irr}<span class="unit">%</span>`;
        document.querySelector('.stat-grid .stat:nth-child(3) .value').innerHTML = `${data.financials.price_per_m2}<span class="unit">Tr</span>`;

        document.querySelector('.persona-highlight h4').textContent = data.persona;
        document.querySelector('.persona-highlight p').textContent = data.persona_desc;

        document.querySelector('.message-box p').textContent = data.sale_script;
        
        // Export Logic
        document.getElementById('btn-download-master').onclick = () => {
            downloadString("MASTER_PACKAGE.json", JSON.stringify(data, null, 2));
        };
        
        document.getElementById('btn-download-client').onclick = () => {
            const reportContent = `BÁO CÁO PHÂN TÍCH ĐẦU TƯ BẤT ĐỘNG SẢN IQI (MẢT)\n\n` +
            `DỰ ÁN: ${data.project}\nĐIỂM ĐẦU TƯ: ${data.score} / 10\n\n` +
            `[1] THÔNG SỐ TÀI CHÍNH\n- Lợi Suất Thuê Hằng Năm: ${data.financials.yield}%\n` +
            `- Tỷ Suất Sinh Lời Nội Bộ (IRR 5 năm): ${data.financials.irr}%\n` +
            `- Chốt Giá Giao Dịch: ${data.financials.price_per_m2} Tr/m2\n\n` +
            `[2] BẢN THUYẾT MINH KHÁCH HÀNG (PERSONA)\n- Chân Dung: ${data.persona}\n- Động Cơ Mua: ${data.persona_desc}\n\n` +
            `[3] KỊCH BẢN CHỐT GIAO DỊCH (M5)\n${data.sale_script}\n\n` +
            `================\n[Hệ thống Sinh Tự Động Bằng Gemini 2.5 Pro - IQI Real Estate AI]`;
            downloadString(`CLIENT_REPORT_${data.project}.txt`, reportContent);
        };

        loadingView.classList.add('hidden');
        resultView.classList.remove('hidden');
    }

    btnRecreate.addEventListener('click', () => {
        // Reset and go back
        resultView.classList.add('hidden');
        inputView.classList.remove('hidden');
        aiForm.reset();
    });
});
